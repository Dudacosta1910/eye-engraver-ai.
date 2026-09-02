# Eye Engraver AI — Complete Local MVP

Aplicativo web local para preparação automática de imagens de olhos/sobrancelhas
destinadas à gravação personalizada.

## Incluído

- Login único
- Dashboard
- Upload de imagem
- Detecção de olhos/sobrancelhas com MediaPipe
- Métricas de qualidade
- Tratamento P&B não-generativo
- Crop inteligente 4,5:1
- Ajustes manuais opcionais
- Resize determinístico para 900×200
- Validação técnica
- Histórico visual
- Busca por pedido
- Salvamento de original, tratada e final
- Download da imagem final
- Layout dark moderno

## Instalação

Recomendado: Python 3.11.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Abra:

http://localhost:8501

## Login inicial

Usuário: `admin`

Senha: `1234`

## Importante

Esse login é somente para a versão local. Para produção:
- usar autenticação segura;
- senha com hash;
- variáveis de ambiente;
- HTTPS;
- banco de dados;
- armazenamento privado de imagens.

## Estrutura

```text
eye_engraver_ai_complete/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── services/
│   ├── image_analysis.py
│   ├── image_enhancement.py
│   ├── smart_crop.py
│   ├── validator.py
│   └── storage.py
└── data/
    ├── originals/
    ├── processed/
    ├── final/
    └── records/
```
