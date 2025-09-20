import os, requests, pandas as pd, streamlit as st, plotly.graph_objects as go

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

st.set_page_config(page_title="FinApp", layout="wide")

if "run_id" not in st.session_state:
    st.session_state.run_id = None
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "payload" not in st.session_state:
    st.session_state.payload = None
if "financials" not in st.session_state:
    st.session_state.financials = None
if "ratios" not in st.session_state:
    st.session_state.ratios = None

st.title("📄 FinApp — Extracción + HITL + Ratios")

tab1, tab2, tab3 = st.tabs(["1) Upload & Extract", "2) Revisión (HITL)", "3) Dashboard & What-if"])

with tab1:
    st.subheader("Sube un estado financiero (PDF/imagen/Excel/CSV)")
    period = st.text_input("Periodo", value="2024Q4")
    currency = st.text_input("Moneda", value="MXN")
    f = st.file_uploader("Archivo", type=["pdf","png","jpg","jpeg","csv","xls","xlsx"])
    if st.button("Extraer", type="primary") and f:
        with st.spinner("Procesando…"):
            files = {"file": (f.name, f.getvalue(), f.type)}
            data = {"period": period, "currency": currency, "language": "es"}
            r = requests.post(f"{API_BASE}/ingest", files=files, data=data, timeout=120)
        if r.ok:
            resp = r.json()
            st.session_state.run_id = resp["run_id"]
            st.session_state.doc_id = resp["doc_id"]
            if resp["status"] == "NEEDS_REVIEW":
                st.session_state.payload = resp
                st.success("Se requiere revisión humana (HITL). Ve a la pestaña 2.")
            else:
                st.session_state.financials = resp["financials"]
                st.session_state.ratios = resp["ratios"]
                st.success("¡Listo! Ve a Dashboard.")
        else:
            st.error(f"Error: {r.text}")

with tab2:
    st.subheader("Revisión humana (HITL)")
    if not st.session_state.payload:
        st.info("Primero sube un documento en la pestaña 1.")
    else:
        payload = st.session_state.payload
        st.write(f"**Run:** {st.session_state.run_id}  **Periodo:** {payload.get('period')}  **Moneda:** {payload.get('currency')}  **Escala detectada:** {payload.get('scale_hint') or 'UNIDAD'}")

        # Issues
        if payload.get("issues"):
            st.warning("Issues detectados:")
            for it in payload["issues"]:
                st.write(f"- [{it['severity']}] {it['code']}: {it['message']}")

        # Tabla editable
        df = pd.DataFrame(payload["fields"])
        # Solo mostramos columnas importantes
        show = df[["path","value","unit","confidence"]].copy()
        show.rename(columns={"value":"value_extracted"}, inplace=True)
        edited = st.data_editor(show, num_rows="dynamic", use_container_width=True)

        # Confirmación de escala
        scale = st.selectbox("Confirma la escala:", options=["UNIDAD","MILES","MILLONES"], index=["UNIDAD","MILES","MILLONES"].index(payload.get("scale_hint") or "UNIDAD"))
        currency_sel = st.text_input("Confirma moneda", value=payload.get("currency") or "MXN")

        if st.button("Aplicar correcciones y continuar", type="primary"):
            corrections = []
            for idx, row in edited.iterrows():
                path = row["path"]
                new_v = row.get("value_extracted")
                # sólo si cambió (simple)
                orig = df.loc[idx, "value"]
                if pd.isna(new_v) and pd.isna(orig):
                    continue
                if new_v != orig:
                    corrections.append({"path": path, "new_value": None if pd.isna(new_v) else float(new_v), "reason": "UI edit"})

            # escala/moneda
            corrections.append({"path": "meta.scale_confirmed", "new_value": scale})
            corrections.append({"path": "meta.currency_confirmed", "new_value": currency_sel})

            with st.spinner("Revalidando…"):
                r = requests.post(f"{API_BASE}/review", json={"run_id": st.session_state.run_id, "corrections": corrections}, timeout=120)
            if r.ok:
                resp = r.json()
                if resp["status"] == "NEEDS_REVIEW":
                    st.session_state.payload = resp
                    st.warning("Aún quedan issues. Revisa nuevamente.")
                else:
                    st.session_state.financials = resp["financials"]
                    st.session_state.ratios = resp["ratios"]
                    st.session_state.payload = None
                    st.success("¡Validado! Ve a Dashboard.")
            else:
                st.error(r.text)

with tab3:
    st.subheader("Ratios y What-if")
    if not st.session_state.ratios:
        st.info("Valida primero en la pestaña 2.")
    else:
        ratios = st.session_state.ratios
        # Tarjetas simples
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Ratio", f"{ratios['current_ratio'] if ratios['current_ratio'] is not None else '-':}")
        col2.metric("D/E", f"{ratios['debt_to_equity'] if ratios['debt_to_equity'] is not None else '-'}")
        col3.metric("Gross Margin", f"{ratios['gross_margin']:.2%}" if ratios["gross_margin"] is not None else "-")
        col4.metric("ROE", f"{ratios['roe']:.2%}" if ratios["roe"] is not None else "-")

        # Grafiquita de márgenes
        m = {k:v for k,v in ratios.items() if k in ["gross_margin","operating_margin","net_margin","ebitda_margin"] and v is not None}
        if m:
            fig = go.Figure()
            fig.add_bar(x=list(m.keys()), y=list(m.values()))
            fig.update_layout(height=350, title="Márgenes")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("### Simulación What-if")
        c1, c2 = st.columns(2)
        path = c1.selectbox("Campo", options=[
            "balance.short_term_debt", "balance.inventory", "income.revenue", "income.cogs"
        ])
        new_value = c2.number_input("Nuevo valor (o deja en blanco y usa factor)", value=0.0, step=0.1)
        factor = st.number_input("Factor multiplicativo (opcional)", value=1.0, step=0.05)

        if st.button("Aplicar What-if"):
            changes = []
            if new_value != 0.0:
                changes.append({"path": path, "new_value": new_value})
            else:
                changes.append({"path": path, "factor": factor})
            r = requests.post(f"{API_BASE}/ratios/whatif", json={
                "run_id": st.session_state.run_id,
                "scenario_name": "UI Scenario",
                "changes": changes
            }, timeout=60)
            if r.ok:
                resp = r.json()
                st.session_state.financials = resp["financials"]
                st.session_state.ratios = resp["ratios"]
                st.success("Recalculado.")
            else:
                st.error(r.text)
