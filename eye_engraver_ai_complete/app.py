from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from services.image_analysis import analyze_face
from services.image_enhancement import enhance_for_engraving, auto_recommend
from services.smart_crop import build_smart_crop
from services.validator import validate_final_image
from services.storage import load_jobs, save_job, delete_job

st.set_page_config(
    page_title="Eye Engraver AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#11162A 0%,#0D1222 100%);}
.hero {
    padding: 24px 28px;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(108,99,255,.18), rgba(22,29,52,.92));
    margin-bottom: 18px;
}
.hero h1 {margin:0; font-size: 2rem;}
.hero p {margin:.35rem 0 0 0; color:#B8C0D9;}
.card {
    border:1px solid rgba(255,255,255,.08);
    background:rgba(20,26,45,.82);
    border-radius:18px;
    padding:18px;
}
.metric {
    border:1px solid rgba(255,255,255,.08);
    background:#12182A;
    border-radius:16px;
    padding:16px;
}
.badge-ok {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:rgba(55,211,153,.12); color:#67E8B5; font-weight:700;
}
.badge-warn {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:rgba(255,184,77,.12); color:#FFC46B; font-weight:700;
}
.smallmuted {color:#9AA4BD; font-size:.9rem;}
div.stButton > button, div.stDownloadButton > button {
    border-radius:12px;
    font-weight:700;
    min-height:44px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

APP_USER = "admin"
APP_PASSWORD = "1234"

if "auth" not in st.session_state:
    st.session_state.auth = False
if "current_image" not in st.session_state:
    st.session_state.current_image = None


def bytes_of(image: Image.Image) -> bytes:
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    return bio.getvalue()


def login_view():
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown(
            """
            <div class="hero" style="margin-top:9vh;text-align:center;">
                <div style="font-size:48px;">👁️</div>
                <h1>Eye Engraver AI</h1>
                <p>Preparação automática de imagens para gravação personalizada</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login", border=False):
            user = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar no sistema", use_container_width=True, type="primary")

        if submitted:
            if user == APP_USER and password == APP_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.caption("Versão local de desenvolvimento • Login inicial: admin / 1234")


def top_hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dashboard():
    top_hero("Dashboard", "Visão geral dos processamentos e atalhos rápidos.")
    jobs = load_jobs()

    c1, c2, c3 = st.columns(3)
    c1.metric("Processamentos salvos", len(jobs))
    c2.metric("Aprovados", sum(1 for j in jobs if j.get("status") == "approved"))
    c3.metric("Formato final", "900 × 200 px")

    st.subheader("Últimos trabalhos")
    if not jobs:
        st.info("Nenhum trabalho salvo ainda. Vá em “Novo processamento” para começar.")
        return

    for job in jobs[:6]:
        cols = st.columns([1, 3, 1])
        final_path = Path(job["final_path"])
        if final_path.exists():
            cols[0].image(str(final_path), use_container_width=True)
        cols[1].markdown(f"**{job['job_id']}**")
        cols[1].caption(job.get("created_at", "").replace("T", " "))
        cols[2].success("Aprovado" if job.get("status") == "approved" else "Revisar")


def processing():
    top_hero(
        "Novo processamento",
        "Envie a foto original. O sistema analisa, trata, recorta, redimensiona e valida.",
    )

    uploaded = st.file_uploader(
        "Arraste a foto aqui ou clique para selecionar",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
    )

    if uploaded is None:
        st.markdown(
            """
            <div class="card" style="text-align:center;padding:42px;">
              <div style="font-size:44px;">⬆️</div>
              <h3>Pronto para uma nova imagem</h3>
              <div class="smallmuted">JPG, PNG ou WEBP • Até 30 MB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    original = Image.open(uploaded).convert("RGB")
    analysis = analyze_face(original)
    recommendation = auto_recommend(analysis.get("metrics", {}))

    a, b = st.columns([1.2, 1])
    with a:
        st.subheader("Foto original")
        st.image(original, use_container_width=True)

    with b:
        st.subheader("Análise automática")
        if analysis["ok"]:
            st.markdown('<span class="badge-ok">✓ Região dos olhos detectada</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-warn">⚠ Usando enquadramento de segurança</span>', unsafe_allow_html=True)

        metrics = analysis["metrics"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Nitidez", f"{metrics['sharpness_score']}/100")
        m2.metric("Exposição", f"{metrics['brightness_score']}/100")
        m3.metric("Contraste", f"{metrics['contrast_score']}/100")
        st.caption(recommendation["note"])

    st.divider()
    st.subheader("Tratamento e enquadramento")

    c1, c2, c3 = st.columns(3)
    strength = c1.slider(
        "Tratamento P&B",
        0, 100,
        recommendation["treatment_strength"],
        help="Contraste local, redução de ruído e nitidez controlada."
    )
    vertical = c2.slider(
        "Posição vertical",
        -100, 100, 0,
        help="Negativo sobe o crop; positivo desce."
    )
    distance = c3.slider(
        "Distância do enquadramento",
        85, 145, 105,
        help="Maior = crop mais distante."
    )

    processed = enhance_for_engraving(original, strength / 100)
    final, crop_meta = build_smart_crop(
        processed,
        analysis,
        output_size=(900, 200),
        vertical_bias=vertical / 100,
        crop_scale=distance / 100,
    )
    validation = validate_final_image(final, analysis)

    p1, p2 = st.columns([1, 1])
    with p1:
        st.subheader("Tratada")
        st.image(processed, use_container_width=True)

    with p2:
        st.subheader("Final 900 × 200")
        st.image(final, use_container_width=True)
        if validation["passed"]:
            st.success("✓ Arquivo aprovado pela validação técnica")
        else:
            st.error("Revisão necessária")
            for issue in validation["issues"]:
                st.write(f"• {issue}")

    with st.expander("Detalhes técnicos"):
        st.write({
            "crop_box": crop_meta["crop_box"],
            "crop_size": crop_meta["crop_size"],
            "crop_aspect": round(crop_meta["aspect_ratio"], 4),
            "final_size": final.size,
            "final_aspect": round(final.size[0] / final.size[1], 4),
        })

    st.divider()
    job_id = st.text_input(
        "Identificação do pedido",
        value=datetime.now().strftime("%Y%m%d-%H%M%S")
    )

    x1, x2 = st.columns(2)
    if x1.button("Salvar no histórico", type="primary", use_container_width=True):
        record = save_job(
            job_id,
            original,
            processed,
            final,
            {
                "status": "approved" if validation["passed"] else "review",
                "validation": validation,
                "crop": crop_meta,
                "treatment_strength": strength,
                "vertical": vertical,
                "distance": distance,
            },
        )
        st.success(f"Pedido {record['job_id']} salvo com sucesso.")

    x2.download_button(
        "Baixar PNG final",
        data=bytes_of(final),
        file_name=f"{job_id}_900x200.png",
        mime="image/png",
        use_container_width=True,
    )


def history():
    top_hero("Histórico", "Consulte imagens originais, tratadas e finais já salvas.")
    jobs = load_jobs()

    search = st.text_input("Buscar pedido", placeholder="Digite o ID do pedido")
    if search:
        jobs = [j for j in jobs if search.lower() in j.get("job_id", "").lower()]

    if not jobs:
        st.info("Nenhum registro encontrado.")
        return

    for job in jobs:
        with st.expander(f"{job['job_id']}  •  {job.get('created_at','').replace('T',' ')}"):
            c1, c2, c3 = st.columns(3)
            paths = [
                ("Original", job.get("original_path")),
                ("Tratada", job.get("processed_path")),
                ("Final", job.get("final_path")),
            ]
            for col, (label, path) in zip((c1, c2, c3), paths):
                col.caption(label)
                if path and Path(path).exists():
                    col.image(path, use_container_width=True)

            final_path = Path(job["final_path"])
            d1, d2 = st.columns([1, 1])
            if final_path.exists():
                d1.download_button(
                    "Baixar final",
                    data=final_path.read_bytes(),
                    file_name=final_path.name,
                    mime="image/png",
                    key=f"dl_{job['job_id']}",
                    use_container_width=True,
                )

            if d2.button("Excluir registro", key=f"del_{job['job_id']}", use_container_width=True):
                delete_job(job["job_id"])
                st.success("Registro excluído.")
                st.rerun()


def settings():
    top_hero("Configurações", "Parâmetros gerais desta versão local.")
    st.markdown(
        """
        <div class="card">
          <h3>Saída padrão</h3>
          <p>900 × 200 px • Proporção 4,5:1 • PNG • Preto e branco</p>
          <h3>Política de edição</h3>
          <p>Tratamento não-generativo. O sistema não cria olhos, sobrancelhas ou áreas ausentes.</p>
          <h3>Armazenamento</h3>
          <p>Esta versão salva os arquivos localmente na pasta <code>data/</code>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning("Antes de publicar na internet, troque o login local por autenticação segura e use armazenamento privado.")


def app_shell():
    with st.sidebar:
        st.markdown("## 👁️ Eye Engraver AI")
        st.caption("Engraving Image Studio")
        st.divider()

        page = st.radio(
            "Navegação",
            ["Dashboard", "Novo processamento", "Histórico", "Configurações"],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("Sistema")
        st.write("🟢 Motor de imagem ativo")
        st.write("📐 Saída: 900 × 200")
        st.write("🖼️ Histórico: local")

        st.divider()
        if st.button("Sair", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    if page == "Dashboard":
        dashboard()
    elif page == "Novo processamento":
        processing()
    elif page == "Histórico":
        history()
    else:
        settings()


if not st.session_state.auth:
    login_view()
else:
    app_shell()
