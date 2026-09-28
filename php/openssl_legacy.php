<?php
declare(strict_types=1);

function enablePortableOpenSslLegacyProvider(): void
{
    $runtimeDir = dirname(__DIR__) . DIRECTORY_SEPARATOR . 'runtime' . DIRECTORY_SEPARATOR . 'php';
    $configPath = $runtimeDir . DIRECTORY_SEPARATOR . 'openssl-legacy.cnf';

    if (is_file($configPath) && (getenv('OPENSSL_CONF') === false || getenv('OPENSSL_CONF') === '')) {
        putenv('OPENSSL_CONF=' . $configPath);
        $_ENV['OPENSSL_CONF'] = $configPath;
    }

    if (getenv('OPENSSL_MODULES') !== false && getenv('OPENSSL_MODULES') !== '') {
        return;
    }

    $moduleDirs = [
        $runtimeDir . DIRECTORY_SEPARATOR . 'extras' . DIRECTORY_SEPARATOR . 'ssl',
        $runtimeDir . DIRECTORY_SEPARATOR . 'lib' . DIRECTORY_SEPARATOR . 'ossl-modules',
        $runtimeDir . DIRECTORY_SEPARATOR . 'ossl-modules',
    ];

    foreach ($moduleDirs as $moduleDir) {
        if (is_dir($moduleDir)) {
            putenv('OPENSSL_MODULES=' . $moduleDir);
            $_ENV['OPENSSL_MODULES'] = $moduleDir;
            return;
        }
    }

    if (!is_dir($runtimeDir)) {
        return;
    }

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($runtimeDir, FilesystemIterator::SKIP_DOTS)
    );

    foreach ($iterator as $file) {
        if (!$file->isFile()) {
            continue;
        }

        $filename = strtolower($file->getFilename());
        if ($filename === 'legacy.dll' || $filename === 'legacy.so') {
            $moduleDir = $file->getPath();
            putenv('OPENSSL_MODULES=' . $moduleDir);
            $_ENV['OPENSSL_MODULES'] = $moduleDir;
            return;
        }
    }
}

enablePortableOpenSslLegacyProvider();
