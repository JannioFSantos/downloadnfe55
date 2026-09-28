# downloadnfe55

Ferramenta desktop para baixar **NF-e modelo 55 destinadas ao CNPJ** usando o serviço oficial **Distribuição DF-e (NFeDistribuicaoDFe)**, certificado digital A1 e o projeto open source [NFePHP/SPED-NFe](https://github.com/nfephp-org/sped-nfe).

A interface desktop é feita em Python/Tkinter e o motor fiscal utiliza NFePHP.

## Recursos

- seleção de certificado A1 `.pfx` ou `.p12`;
- consulta oficial da Distribuição DF-e;
- controle automático do `ultNSU`;
- armazenamento separado de:
  - XML completo `procNFe`;
  - resumo `resNFe`;
  - eventos;
- tela para visualizar documentos encontrados;
- manifestação **Ciência da Operação** somente após confirmação do usuário;
- sem Selenium, Chrome ou ChromeDriver;
- versão portátil para Windows com PHP e dependências incluídos.

## Versão portátil para Windows

Baixe o pacote pronto aqui: [DownloadNFe55-windows-portable](https://github.com/JannioFSantos/downloadnfe55/actions/runs/36433689795/artifacts/10973929582).

Depois de baixar, extraia o ZIP e abra `DownloadNFe55.exe`. Não é necessário instalar Python, PHP ou Composer no computador do usuário final.

O pacote portátil gerado pelo build fica assim:

```text
DownloadNFe55/
├── DownloadNFe55.exe
├── runtime/
│   └── php/
│       ├── php.exe
│       ├── php.ini
│       ├── openssl-legacy.cnf
│       └── ext/
├── php/
│   ├── distribuicao.php
│   ├── manifestacao.php
│   └── openssl_legacy.php
└── vendor/
    └── NFePHP e dependências Composer
```

Ao executar, o aplicativo procura o PHP nesta ordem:

```text
1. runtime/php/php.exe dentro do pacote portátil
2. php.exe instalado no Windows e disponível no PATH
3. mensagem clara informando que o Runtime PHP não foi encontrado
```

### Erro ao ler certificado A1

Se aparecer o erro `error:0308010c:digital envelope routines::unsupported`, baixe novamente a versão portátil mais recente. Esse erro ocorre com alguns certificados A1 exportados com criptografia antiga; o pacote portátil inclui uma configuração OpenSSL compatível para esse caso.

Se o erro continuar, exporte novamente o certificado A1 pelo Windows usando uma criptografia mais atual, de preferência AES/SHA-256, e tente com o novo arquivo `.pfx` ou `.p12`.

## Fluxo

```text
CNPJ + UF + Certificado A1
          ↓
      NFePHP
          ↓
NFeDistribuicaoDFe
          ↓
       ultNSU
          ↓
 ┌────────┴────────┐
 │                 │
procNFe          resNFe
 │                 │
XML completo    resumo
                   ↓
          Ciência da Operação
                   ↓
          nova sincronização
                   ↓
             XML completo
```

O **NSU não é o número da NF-e**. Ele é o sequencial utilizado pela Distribuição DF-e. O aplicativo guarda automaticamente o último NSU processado para continuar as consultas sem reiniciar do zero.

## Requisitos para desenvolvimento

Para rodar a partir do código-fonte ou gerar o pacote localmente:

- Python 3.10 ou superior;
- PHP 8.1 ou superior;
- Composer;
- extensões PHP exigidas pelo NFePHP;
- certificado digital A1 válido.

## Instalação para desenvolvimento

```bash
git clone https://github.com/JannioFSantos/downloadnfe55.git
cd downloadnfe55
composer install
python app.py
```

## Gerar pacote portátil localmente

No Windows, com Python, PHP e Composer instalados:

```bat
build_windows.bat
```

O arquivo final será criado em:

```text
package/DownloadNFe55-windows-portable.zip
```

## Gerar pacote pelo GitHub Actions

O workflow **Windows portable package** gera automaticamente o ZIP portátil em Windows. Ele instala Python, PHP e Composer no ambiente do GitHub, baixa as dependências Composer, copia o PHP para `runtime/php` e publica o artefato `DownloadNFe55-windows-portable`.

Também é possível executar o workflow manualmente pela aba **Actions** do GitHub.

## Estrutura do código-fonte

```text
downloadnfe55/
├── app.py
├── composer.json
├── requirements.txt
├── build_windows.bat
├── tools/
│   └── prepare_portable_php.ps1
├── .github/
│   └── workflows/
│       └── windows-portable.yml
├── php/
│   ├── distribuicao.php
│   ├── manifestacao.php
│   └── openssl_legacy.php
└── README.md
```

## Segurança

Não envie certificado A1, senha ou XML real para o GitHub.

Os arquivos `*.pfx`, `*.p12`, `runtime/`, `vendor/` e os arquivos de estado do NSU ficam ignorados pelo Git.

A senha do certificado é utilizada somente durante a execução e não deve ser salva no repositório.

## Manifestação

A manifestação não é automática. O usuário deve selecionar uma NF-e resumida e confirmar explicitamente a **Ciência da Operação** antes do envio à SEFAZ.

## Autor

**Jannio F. Santos**

GitHub: [@JannioFSantos](https://github.com/JannioFSantos)

## Aviso

Projeto open source em desenvolvimento. Antes de utilizar em produção, valide o funcionamento com certificado de teste/empresa e consulte a documentação vigente da NF-e.
