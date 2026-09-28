<?php
declare(strict_types=1);

require __DIR__ . '/openssl_legacy.php';
require dirname(__DIR__) . '/vendor/autoload.php';

use NFePHP\Common\Certificate;
use NFePHP\NFe\Tools;

function arg(array $args, string $name): string {
    $key = array_search("--{$name}", $args, true);
    if ($key === false || !isset($args[$key + 1])) {
        throw new InvalidArgumentException("Parâmetro obrigatório ausente: --{$name}");
    }
    return (string) $args[$key + 1];
}

function emit(array $data): void {
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . PHP_EOL;
}

function digits(string $value): string {
    return preg_replace('/\D+/', '', $value) ?? '';
}

try {
    $cnpj = digits(arg($argv, 'cnpj'));
    $uf = strtoupper(arg($argv, 'uf'));
    $certPath = arg($argv, 'cert');
    $password = arg($argv, 'password');
    $chave = digits(arg($argv, 'chave'));

    if (strlen($cnpj) !== 14) {
        throw new RuntimeException('CNPJ inválido.');
    }

    if (strlen($chave) !== 44) {
        throw new RuntimeException('Chave de acesso inválida.');
    }

    $config = [
        'atualizacao' => date('Y-m-d H:i:s'),
        'tpAmb' => 1,
        'razaosocial' => 'downloadnfe55',
        'siglaUF' => $uf,
        'cnpj' => $cnpj,
        'schemes' => 'PL_009_V4',
        'versao' => '4.00',
        'tokenIBPT' => '',
        'CSC' => '',
        'CSCid' => '',
        'proxyConf' => [
            'proxyIp' => '',
            'proxyPort' => '',
            'proxyUser' => '',
            'proxyPass' => '',
        ],
    ];

    $certificate = Certificate::readPfx(
        (string) file_get_contents($certPath),
        $password
    );

    $tools = new Tools(
        json_encode($config, JSON_UNESCAPED_UNICODE),
        $certificate
    );

    $tools->model('55');
    $tools->setEnvironment(1);

    // tpEvento 1 no método do NFePHP representa Ciência da Operação.
    $response = $tools->sefazManifesta(
        $chave,
        1,
        '',
        date('Y-m-d\TH:i:sP')
    );

    $dom = new DOMDocument();

    if (!$dom->loadXML($response)) {
        throw new RuntimeException('Resposta inválida da SEFAZ.');
    }

    $cStatNodes = $dom->getElementsByTagName('cStat');
    $xMotivoNodes = $dom->getElementsByTagName('xMotivo');

    $cStat = $cStatNodes->length
        ? trim((string) $cStatNodes->item($cStatNodes->length - 1)->nodeValue)
        : '';

    $xMotivo = $xMotivoNodes->length
        ? trim((string) $xMotivoNodes->item($xMotivoNodes->length - 1)->nodeValue)
        : '';

    emit([
        'status' => 'concluido',
        'cStat' => $cStat,
        'xMotivo' => $xMotivo,
        'chave' => $chave,
    ]);

} catch (Throwable $e) {
    emit([
        'status' => 'erro',
        'mensagem' => $e->getMessage(),
    ]);
    exit(1);
}
