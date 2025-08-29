# 🤖 Bot_WnS (What's New SEFAZ?)

Bot para monitorar alterações em conteúdos da **SEFAZ** (ou qualquer página) e enviar alertas no **Discord** via **Webhook**.  
O nome **WnS** vem de *What's New SEFAZ*, já que o objetivo principal é notificar sobre mudanças importantes, como **Notas Técnicas** e **Esquemas XML**.

---

## 🚀 Funcionalidades

- ✅ Monitora múltiplas páginas ao mesmo tempo.
- ✅ Identifica alterações em conteúdos HTML específicos.
- ✅ Ignora blocos de estatísticas dinâmicas para evitar falsos positivos.
- ✅ Envia alertas automáticos para um canal do **Discord**.
- ✅ Mensagem de alerta personalizada com **nome amigável** (label) para cada URL.
- ✅ Suporte para adicionar **infinitas URLs** via `urls.json`.
- ✅ Armazena snapshots para detectar mudanças.

---

## 📂 Estrutura do Projeto

Bot_WnS/
├── monitor.py # Script principal
├── urls.json # URLs monitoradas + labels
├── discord.txt # Credenciais e Webhook do Discord
├── snapshot.json # Armazena os hashes de cada URL
├── .gitignore # Arquivos ignorados no GitHub
└── README.md # Este arquivo


---

## ⚙️ Configuração

### **1. Clonar o repositório**

git clone https://github.com/Luuusca/Bot_WnS.git
cd Bot_WnS

### **2. Criar ambiente virtual (opcional, mas recomendado)**
python -m venv venv
venv\Scripts\activate

### **3. Instalar dependências**