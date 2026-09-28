# downloadnfe55

Ferramenta desktop que estou desenvolvendo para baixar **NF-e modelo 55 destinadas ao CNPJ** usando o serviço oficial **Distribuição DF-e (NFeDistribuicaoDFe)**, certificado digital A1 e o projeto open source [NFePHP/SPED-NFe](https://github.com/nfephp-org/sped-nfe).

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
- preparado para futura distribuição em Windows.

## Fluxo

```
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

## Requisitos

- Python 3.10 ou superior;
- PHP 8.1 ou superior;
- Composer;
- extensões PHP exigidas pelo NFePHP;
- certificado digital A1 válido.

## Instalação

```bash
git clone https://github.com/JannioFSantos/downloadnfe55.git
cd downloadnfe55
composer install
python app.py
```

## Estrutura

```
downloadnfe55/
├── app.py
├── composer.json
├── requirements.txt
├── .gitignore
├── php/
│   ├── distribuicao.php
│   └── manifestacao.php
└── README.md
```

## Segurança

Não envie certificado A1, senha ou XML real para o GitHub.

Os arquivos `*.pfx`, `*.p12` e os arquivos de estado do NSU ficam ignorados pelo Git.

A senha do certificado é utilizada somente durante a execução e não deve ser salva no repositório.

## Manifestação

A manifestação não é automática. O usuário deve selecionar uma NF-e resumida e confirmar explicitamente a **Ciência da Operação** antes do envio à SEFAZ.

## Autor

**Jannio F. Santos**

GitHub: [@JannioFSantos](https://github.com/JannioFSantos)

## Aviso

Projeto open source em desenvolvimento. Antes de utilizar em produção, valide o funcionamento com certificado de teste/empresa e consulte a documentação vigente da NF-e.
