<?php
declare(strict_types=1);

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
    $output = rtrim(arg($argv, 'output'), DIRECTORY_SEPARATOR);

    if (strlen($cnpj) !== 14) {
        throw new RuntimeException('CNPJ inválido.');
    }

    if (!is_file($certPath)) {
        throw new RuntimeException('Certificado A1 não encontrado.');
    }

    if (!is_dir($output) && !mkdir($output, 0775, true) && !is_dir($output)) {
        throw new RuntimeException('Não foi possível criar a pasta de saída.');
    }

    $stateFile = $output . DIRECTORY_SEPARATOR . '.nfe-state-' . $cnpj . '.json';
    $state = is_file($stateFile)
        ? json_decode((string) file_get_contents($stateFile), true)
        : [];

    $ultNSU = str_pad((string) ($state['ultNSU'] ?? '0'), 15, '0', STR_PAD_LEFT);

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

    $xmlCompletos = 0;
    $resumos = 0;
    $eventos = 0;
    $maxNSU = $ultNSU;
    $consultas = 0;
    $limiteConsultas = 10;

    emit([
        'status' => 'inicio',
        'ultNSU' => $ultNSU,
    ]);

    do {
        $consultas++;

        $response = $tools->sefazDistDFe((int) $ultNSU);

        $dom = new DOMDocument();
        if (!$dom->loadXML($response)) {
            throw new RuntimeException('A SEFAZ retornou XML inválido.');
        }

        $ret = $dom->getElementsByTagName('retDistDFeInt')->item(0);

        if (!$ret) {
            throw new RuntimeException('retDistDFeInt não encontrado na resposta.');
        }

        $get = static function (DOMNode $node, string $tag): string {
            $nodes = $node->getElementsByTagName($tag);
            return $nodes->length ? trim((string) $nodes->item(0)->nodeValue) : '';
        };

        $cStat = $get($ret, 'cStat');
        $xMotivo = $get($ret, 'xMotivo');
        $novoUltNSU = $get($ret, 'ultNSU') ?: $ultNSU;
        $maxNSU = $get($ret, 'maxNSU') ?: $novoUltNSU;

        emit([
            'status' => 'consulta',
            'cStat' => $cStat,
            'xMotivo' => $xMotivo,
            'ultNSU' => $novoUltNSU,
            'maxNSU' => $maxNSU,
        ]);

        $lote = $ret->getElementsByTagName('loteDistDFeInt')->item(0);

        if ($lote) {
            foreach ($lote->getElementsByTagName('docZip') as $docZip) {
                $nsu = $docZip->getAttribute('NSU');
                $schema = $docZip->getAttribute('schema');

                $binary = base64_decode(trim((string) $docZip->nodeValue), true);
                if ($binary === false) {
                    continue;
                }

                $xml = gzdecode($binary);
                if ($xml === false) {
                    continue;
                }

                if (str_starts_with($schema, 'procNFe')) {
                    $folder = 'xml';
                    $xmlCompletos++;
                } elseif (str_starts_with($schema, 'resNFe')) {
                    $folder = 'resumos';
                    $resumos++;
                } else {
                    $folder = 'eventos';
                    $eventos++;
                }

                $dir = $output . DIRECTORY_SEPARATOR . $folder;

                if (!is_dir($dir)) {
                    mkdir($dir, 0775, true);
                }

                $safeSchema = preg_replace('/[^A-Za-z0-9_.-]/', '_', $schema);
                $filename = $nsu . '-' . $safeSchema . '.xml';

                file_put_contents(
                    $dir . DIRECTORY_SEPARATOR . $filename,
                    $xml
                );
            }
        }

        $ultNSU = str_pad($novoUltNSU, 15, '0', STR_PAD_LEFT);
        $maxNSU = str_pad($maxNSU, 15, '0', STR_PAD_LEFT);

        file_put_contents(
            $stateFile,
            json_encode([
                'ultNSU' => $ultNSU,
                'maxNSU' => $maxNSU,
                'updated_at' => date(DATE_ATOM),
            ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
        );

        if ($cStat === '137' || $cStat === '656') {
            break;
        }

        if ($ultNSU === $maxNSU) {
            break;
        }

        if ($consultas >= $limiteConsultas) {
            break;
        }

        sleep(2);

    } while (true);

    emit([
        'status' => 'concluido',
        'xml_completos' => $xmlCompletos,
        'resumos' => $resumos,
        'eventos' => $eventos,
        'ultNSU' => $ultNSU,
        'maxNSU' => $maxNSU,
        'consultas' => $consultas,
    ]);

} catch (Throwable $e) {
    emit([
        'status' => 'erro',
        'mensagem' => $e->getMessage(),
    ]);
    exit(1);
}
