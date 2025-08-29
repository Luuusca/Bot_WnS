# 🤖 Bot_WnS (What's New SEFAZ?)

Bot para monitorar alterações em conteúdos de sites da **SEFAZ** (e outros) e enviar alertas no **Discord** via **Webhook**.  
O nome **WnS** vem de *What's New SEFAZ*, pois o objetivo é detectar e notificar mudanças importantes, como **Notas Técnicas**, **Esquemas XML** e documentos fiscais em geral.
---

## 🚀 Funcionalidades

- ✅ Monitora **múltiplas páginas** simultaneamente.
- ✅ Aceita **selectores CSS personalizados** por URL.
- ✅ Possui **fallback automático** caso o seletor não seja encontrado.
- ✅ Ignora **blocos de estatísticas dinâmicas** para evitar falsos alertas.
- ✅ Envia mensagens automáticas no **Discord** com nome amigável.
- ✅ Suporte para adicionar novas URLs facilmente via `urls.json`.
- ✅ Salva **snapshots independentes por ID** para rastrear mudanças.
- ✅ Permite compilar para **.exe** com um simples `build.bat`.

## 📂 Estrutura do Projeto

Bot_WnS/
├── monitor.py          # Script principal
├── urls.json           # Lista de URLs e labels monitorados
├── discord.txt         # Credenciais do Discord Webhook
├── snapshot.json       # Hashes dos conteúdos monitorados
├── build.bat           # Compila o projeto em um .exe automaticamente
├── dist/               # (Gerado após compilação) Contém o executável
├── .venv/              # Ambiente virtual do Python
├── .gitignore          # Arquivos ignorados no GitHub
└── README.md           # Este arquivo

---

## ⚙️ Configuração do Ambiente

### **1. Clonar o repositório**

git clone https://github.com/SEU_USUARIO/Bot_WnS.git
cd Bot_WnS

### **2. Criar ambiente virtual**

python -m venv .venv

### **3. Ativar ambiente virtual**

- PowerShell:

.\.venv\Scripts\Activate.ps1

- CMD:

.\.venv\Scripts\activate.bat

### **4. Instalar dependências**
pip install -r requirements.txt

---

Se não existir requirements.txt, instale manualmente:

pip install selenium beautifulsoup4 requests pyinstaller

### **🔑 Configuração do Discord (discord.txt)**

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/SEU_WEBHOOK
USERNAME=Bot WnS
AVATAR_URL=
MENTION_ROLE_ID=

Onde:

- DISCORD_WEBHOOK_URL → URL do webhook do Discord.
- USERNAME → Nome exibido no Discord.
- AVATAR_URL (opcional) → Link para avatar do bot, se houver.
- MENTION_ROLE_ID → Menciona um cargo no discord, opcional, funciona sem também.

## **🌐 Configuração das URLs (urls.json)**

Defina todas as páginas a monitorar no urls.json:

{
  "items": [
    {
      "id": 1,
      "label": "Nota Técnica",
      "url": "https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY="
    },
    {
      "id": 2,
      "label": "Esquemas XML",
      "url": "https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=BMPFMBoln3w="
    },
    {
      "id": 5,
      "label": "Informes Técnicos - MDF-e",
      "url": "https://dfe-portal.svrs.rs.gov.br/Mdfe/Avisos",
      "selector": "main"
    },
    {
      "id": 6,
      "label": "Documentos MDF-e",
      "url": "https://dfe-portal.svrs.rs.gov.br/Mdfe/Documentos",
      "selector": "main"
    }
  ]
}


Onde:

- id → Identificador único.
- label → Nome amigável que aparecerá na mensagem do Discord.
- url → Página a ser monitorada.
- selector (opcional) → CSS selector personalizado.


### **▶️ Como Usar**

Rodar no VS Code / Terminal:

python monitor.py --log-level INFO

Opções disponíveis
- --no-headless → Abre o Chrome visível.
- --log-level DEBUG → Exibe detalhes extras.
- --quiet-ok → Oculta mensagens de páginas sem alterações.

Exemplo:

python monitor.py --no-headless --log-level DEBUG
---

### **🧰 Compilando para .EXE

1. Criar o executável
Rode no terminal do VS Code:

- .\build.bat

O .bat faz automaticamente:

- Ativa o venv.
- Instala/atualiza o PyInstaller.
- Compila o .exe na pasta dist.

O executável final estará em:

Bot_WnS\dist\Bot_WnS.exe
---

### **📌 Mensagens no Discord**

Exemplo de mensagem enviada pelo bot:
Houve alteração em **Nota Técnica**:
https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=


🛠 Tecnologias Usadas

Python 3.10+
Selenium → Web scraping automatizado.
BeautifulSoup4 → Parsing e limpeza de HTML.
Requests → Envio de mensagens ao Discord.
PyInstaller → Geração de executável.
---

🧾 Licença
Este projeto foi desenvolvido para uso interno, mas pode ser adaptado para qualquer tipo de monitoramento.
---

⭐ Dica
Para adicionar novas páginas, basta incluir novos itens no urls.json.
O bot passa a monitorá-las automaticamente, sem alterar o código.