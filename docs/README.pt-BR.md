<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**POC interno de recompensa diária do QuWork: verificar status, registrar intenção, resgatar e reler**

> Version: **v0.1.0** (script 2026-11-12 · release 2026-11-24) · Status: `implemented_unverified`

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **[Português (BR)](README.pt-BR.md)**

Status primeiro · ledger confirming · releitura do claim · renovação de token · multicon­ta · notificações opcionais

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

</div>

---

<a id="policy"></a>
## Limites de uso

O QuWork Daily é um POC interno para proprietários de contas manterem suas próprias recompensas diárias. O repositório e as instruções permanecem gratuitos. Não redistribua como produto pago, não se passe pelo autor e não remova a atribuição.

O estado do protocolo é `implemented_unverified`. Os testes provam a consistência do fluxo; uma conta real ainda precisa de releitura no servidor antes de declarar sucesso.

---

<a id="overview"></a>
## Visão em 30 segundos

| Item | Descrição |
| :--- | :--- |
| **Objetivo** | Ler o status, resgatar quando disponível e confirmar o resultado. |
| **Entrada** | `QUWORK_ACCOUNTS` ou `QUWORK_ACCESS_TOKEN`. |
| **Proteção** | Salvar `confirming` antes do primeiro claim e não reenviar em caso incerto. |
| **Saídas** | `query`, `done`, `claimed`, `inactive`, `pending`, `failed`. |
| **Execução** | Windows, Linux, Qinglong ou GitHub Actions manual. |
| **Release** | `v0.1.0`, POC interno publicado como [GitHub Release](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0). |

---

<a id="what"></a>
## O que é

O QuWork Daily é um executor de arquivo único com uma máquina de estados estrita. Ele lê o status, registra a intenção, envia o claim uma vez e relê o status.

`quwork_get_token.py` lê o SQLite do cliente local em modo somente leitura. Por padrão mascara as credenciais e só imprime o JSON completo com `--export`.

---

<a id="protocol"></a>
## Protocolo e releitura

| Item | Valor atual |
| :--- | :--- |
| URL base | `https://llm.rrzu.com` |
| Versão do cliente | `1.6.0` |
| Status | `GET /api/user/daily-reward/status` |
| Claim | `POST /api/user/daily-reward/claim` |
| Renovação | `GET /api/user/refresh` |
| Cabeçalho de ambiente | `X-QurWork-Env: prod` |
| Cabeçalho de versão | `X-QurWork-Version: 1.6.0` |

O status deve conter `claimed` e `can_claim` booleanos, `points` numérico, `consecutive_days` inteiro e `next_refresh_at` válido. O claim só é confirmado quando a releitura retorna `claimed=true` com o mesmo `next_refresh_at`.

---

<a id="credentials"></a>
## Credenciais e contas

| Variável | Obrigatória | Descrição |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | uma de duas | Array JSON ou objeto com `accessToken` |
| `QUWORK_ACCESS_TOKEN` | uma de duas | Bearer token de uma conta |
| `QUWORK_PROXY` | Não | Proxy HTTP/HTTPS global |
| `QUWORK_STATE_DIR` | Não | Diretório de estado |
| `QUWORK_QUERY_ONLY` | Não | `1` ativa modo somente leitura |

Campos `accessToken`, `access_token` ou `token` aninhados em `secret`, `session`, `data`, `auth` e `user` também são reconhecidos.

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

---

<a id="quickstart"></a>
## Início rápido

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

Para várias contas:

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"main","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

Execute `--query` primeiro e confirme o contrato antes de habilitar claims.

---

<a id="qinglong"></a>
## Qinglong

| Etapa | Ação |
| :---: | :--- |
| 1 | Envie `quwork_daily.py` e, opcionalmente, `quwork_get_token.py`. |
| 2 | Instale `requests>=2.25.0`. |
| 3 | Configure `QUWORK_ACCOUNTS` ou `QUWORK_ACCESS_TOKEN`. |
| 4 | Defina um `QUWORK_STATE_DIR` persistente. |
| 5 | Comece com `task quwork_daily.py --query` e depois use o comando normal. |

O diretório de estado precisa sobreviver entre execuções para recuperar tokens renovados e claims `confirming`.

---

<a id="actions"></a>
## GitHub Actions

O repositório ainda não inclui `.github/workflows`. Em um Actions privado, use estes Secrets:

| Secret | Obrigatório | Descrição |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | uma de duas | JSON de várias contas |
| `QUWORK_ACCESS_TOKEN` | uma de duas | Token de uma conta |
| `QUWORK_PROXY` | Não | URL do proxy |

O arquivo de estado contém um access token renovado. Não o publique como artifact comum.

---

<a id="cli"></a>
## CLI e variáveis de ambiente

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | `1` equivale a `--query` |
| `QUWORK_STATE_DIR` | Diretório do script | Salva `.quwork_state.json` |
| `QUWORK_PROXY` | Vazio | `proxy` da conta tem prioridade |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | Vazio | Notificação WeCom |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | Vazio | Notificação PushPlus |

---

<a id="result-codes"></a>
## Códigos de resultado

| Resultado | Significado | Sucesso |
| :--- | :--- | :---: |
| `query` | Consulta concluída | Neutro |
| `done` | Já resgatado antes desta execução | Sim |
| `claimed` | Resgatado e confirmado por releitura | Sim |
| `inactive` | Indisponível no ciclo atual | Neutro |
| `pending` | Resultado incerto; próxima execução só consulta | Não |
| `failed` | Falha de configuração, autenticação, negócio ou rede | Não |

Código de saída `0` significa nenhuma conta com falha. Código `1` significa erro de configuração ou pelo menos uma falha.

---

<a id="success"></a>
## Critérios de sucesso

Uma conta só é bem-sucedida quando:

1. O objeto de status está completo e com tipos corretos.
2. A conta já está em `claimed=true` ou começa com `claimed=false` e `can_claim=true`.
3. Após o claim, a releitura retorna `claimed=true`.
4. `next_refresh_at` não muda durante o claim.
5. O ledger passa de `confirming` para `claimed`.

Testes unitários não provam que uma conta real recebeu a recompensa.

---

<a id="tests"></a>
## Testes

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

Os sete testes cobrem parsing de sessão, conclusão sem POST, releitura do claim, recuperação pending, renovação única após 401, rejeição explícita e validação estrita de tipos.

---

<a id="design"></a>
## Princípios de design

- **Status primeiro:** não faça claim sem estado conhecido.
- **Registrar intenção:** salve `confirming` antes do primeiro POST.
- **Releitura do servidor:** sucesso exige `claimed=true` e o mesmo reset.
- **Sem POST duplicado:** resultado incerto permanece pending.
- **Contrato estrito:** tipos inválidos causam falha.
- **Estado atômico:** arquivo temporário, `fsync` e `os.replace`.
- **Credenciais mascaradas:** tokens são removidos das mensagens.

---

<a id="privacy"></a>
## Privacidade e segurança

`.quwork_state.json` contém access tokens renovados e deve ser tratado como senha. O arquivo é ignorado pelo Git.

Não publique o arquivo de estado, `QUWORK_ACCOUNTS`, `QUWORK_ACCESS_TOKEN`, saída de `--export`, JWT completo, cookies, telefone, UID ou credenciais de proxy.

---

<a id="layout"></a>
## Estrutura do diretório

```text
QuWork-Daily/
├── assets/
├── docs/
├── tests/test_quwork_daily.py
├── CHANGELOG.md
├── README.md
├── quwork_daily.py
├── quwork_get_token.py
└── requirements.txt
```

---

<a id="release"></a>
## Versão e releases

| Item | Valor atual |
| :--- | :--- |
| Versão do script | `v0.1.0` |
| Data do script | `2026-11-12` |
| Git tag | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) |
| GitHub Release | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) (2026-11-24) |
| Estado do protocolo | `implemented_unverified` |

O release exige releitura real de `can_claim=true` para `claimed=true`, mudança de pontos verificável, `next_refresh_at` inalterado, evidência de regressão para falhas e pacote sem `.quwork_state.json`.

---

<a id="disclaimer"></a>
## Aviso legal

Use este projeto apenas para manter sua própria conta. Confirme a conta, os termos do serviço e as regras aplicáveis antes do uso. O autor não garante status da conta, mudança de pontos, estabilidade da API, disponibilidade de rede ou resultados de implantações de terceiros.

---

<a id="donate"></a>
## QR codes de apoio

A doação é opcional e não afeta código, documentação ou atendimento de Issues.

<div align="center">
<table>
<tr>
<td align="center"><strong>WeChat</strong><br /><img src="../assets/donate-wechat.png" width="260" alt="QR code de doação WeChat" /></td>
<td align="center"><strong>Alipay</strong><br /><img src="../assets/donate-alipay.jpg" width="260" alt="QR code de doação Alipay" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## Feedback e Star History

- [Abrir Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [Abrir Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [Changelog](../CHANGELOG.md)

Inclua logs mascarados, resultado, status HTTP e passos de reprodução. Nunca publique tokens, cookies, banco da conta ou `.quwork_state.json`.

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
