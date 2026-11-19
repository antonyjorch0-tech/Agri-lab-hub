import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import forecasting as fc
from utils.ui import card, hero, note, setup

setup("Forecasting Tools")
hero("Forecasting Tools", "Choose a model, upload your data and get honest, validated results you can download.")

tab_run, tab_dir = st.tabs(["Run an analysis", "Model directory"])


def params_ui(name):
    with st.expander("Model settings (the defaults work for most datasets)"):
        if name in ("XGBoost", "Gradient Boosting"):
            return {"n_estimators": st.slider("Number of trees", 50, 1000, 300, 50),
                    "max_depth": st.slider("Maximum tree depth", 2, 10, 3),
                    "learning_rate": st.select_slider("Learning rate", options=[0.01, 0.03, 0.05, 0.1, 0.2, 0.3], value=0.1)}
        if name in ("Random Forest", "Extra Trees"):
            return {"n_estimators": st.slider("Number of trees", 50, 1000, 300, 50),
                    "max_depth": st.slider("Maximum tree depth", 2, 20, 8)}
        if name == "Support Vector Regression":
            return {"kernel": st.selectbox("Kernel", ["rbf", "linear", "poly"]),
                    "C": st.select_slider("C (penalty)", options=[0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0], value=1.0),
                    "epsilon": st.select_slider("Epsilon", options=[0.01, 0.05, 0.1, 0.2, 0.5], value=0.1)}
        if name == "ANN / MLP":
            return {"hidden": st.slider("Neurons per hidden layer (2 layers)", 4, 128, 32, 4),
                    "alpha": st.select_slider("L2 regularisation", options=[0.0001, 0.001, 0.01, 0.1, 1.0], value=0.001),
                    "max_iter": st.slider("Maximum training iterations", 500, 5000, 2000, 500)}
        if name == "K-Nearest Neighbors":
            return {"k": st.slider("Number of neighbours", 1, 25, 5)}
        st.caption("This model has no settings to adjust.")
        return {}


# ------------------------------------------------------------ model directory
with tab_dir:
    q = st.text_input("Search models", placeholder="Type a model name or family, for example boosting or time series")
    shown = [m for m in fc.CATALOG if q.lower() in m[0].lower() or q.lower() in m[1].lower()]
    if not shown:
        st.info("No model matches that search. Try a shorter word.")
    for i in range(0, len(shown), 3):
        cols = st.columns(3)
        for col, (name, family, ok) in zip(cols, shown[i:i + 3]):
            with col:
                st.markdown(card(name, family, "ready" if ok else "soon"), unsafe_allow_html=True)

# ---------------------------------------------------------------- run analysis
with tab_run:
    up = st.file_uploader("Upload your dataset (.csv, .xlsx or .xls)", type=["csv", "xlsx", "xls"])
    if up is None:
        note("Each row should be one observation (for example one estate in one year) and each column one variable. "
             "Upload a file to begin.")
        st.stop()

    sheets = fc.list_sheets(up)
    sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else (sheets[0] if sheets else None)
    try:
        df = fc.read_upload(up, sheet)
    except Exception as e:
        st.error(f"The file could not be read: {e}")
        st.stop()

    st.caption(f"{len(df):,} rows and {df.shape[1]} columns")
    st.dataframe(df.head(10), use_container_width=True)

    numeric_cols = df.select_dtypes("number").columns.tolist()
    if not numeric_cols:
        st.error("No numeric columns were found. Check that your numbers are stored as numbers, not text.")
        st.stop()

    model_name = st.selectbox("Forecasting model", fc.available_models())
    result_inputs = {}

    if model_name == "ARIMA":
        st.markdown("**ARIMA works on one time series.**")
        c1, c2 = st.columns(2)
        value_col = c1.selectbox("Value to forecast", numeric_cols)
        time_col = c2.selectbox("Time column", list(df.columns))
        c3, c4 = st.columns(2)
        group_col = c3.selectbox("Filter by (optional, for example Estate)", ["(none)"] + list(df.columns))
        group_val = None
        if group_col != "(none)":
            group_val = c4.selectbox("Keep only", sorted(df[group_col].dropna().astype(str).unique()))
        o1, o2, o3 = st.columns(3)
        p_, d_, q_ = (o1.number_input("p (AR)", 0, 5, 1), o2.number_input("d (differencing)", 0, 2, 1),
                      o3.number_input("q (MA)", 0, 5, 1))
        v1, v2 = st.columns(2)
        n_test = v1.number_input("Points held out for validation", 2, 50, 4)
        horizon = v2.number_input("Periods to forecast ahead", 1, 20, 3)
        average = st.checkbox("If several rows share the same period, average them", value=True)

        if st.button("Run ARIMA", type="primary"):
            try:
                sub = df if group_val is None else df[df[group_col].astype(str) == group_val]
                sub = sub[[time_col, value_col]].dropna()
                if sub[time_col].duplicated().any():
                    if not average:
                        raise ValueError("Several rows share the same period. Filter to one group or tick the averaging option.")
                    sub = sub.groupby(time_col, as_index=False)[value_col].mean()
                series = sub.sort_values(time_col).set_index(time_col)[value_col]
                with st.spinner("Fitting ARIMA..."):
                    res = fc.run_arima(series, (int(p_), int(d_), int(q_)), int(n_test), int(horizon))
                res["settings"] = {"Model": "ARIMA", "Order (p,d,q)": str(res["order"]), "Series": value_col,
                                   "Filter": f"{group_col} = {group_val}" if group_val else "none"}
                st.session_state["fc_result"] = res
            except Exception as e:
                st.session_state.pop("fc_result", None)
                st.error(f"Analysis stopped: {e}")
    else:
        target = st.selectbox("Target variable (what you want to predict)", numeric_cols)
        others = [c for c in df.columns if c != target]
        features = st.multiselect("Predictor variables", others,
                                  default=[c for c in numeric_cols if c != target][:8])
        split_label = st.radio("Validation method", ["Chronological hold-out (recommended for yearly or monthly data)",
                                                     "Random hold-out"])
        chrono = split_label.startswith("Chrono")
        time_col = None
        if chrono:
            guess = next((c for c in df.columns if c.lower() in ("year", "date", "time", "period", "month")), df.columns[0])
            time_col = st.selectbox("Time column used for ordering", list(df.columns), index=list(df.columns).index(guess))
        else:
            st.caption("A random split can make results look better than they will be on future years. Use it only if your rows are not ordered in time.")
        test_size = st.slider("Share of rows held out for validation", 0.10, 0.40, 0.20, 0.05)
        params = params_ui(model_name)
        new_up = st.file_uploader("Optional: a file of new rows to predict (same predictor columns)",
                                  type=["csv", "xlsx", "xls"], key="new_data")

        if st.button("Run analysis", type="primary", disabled=not features):
            try:
                new_df = fc.read_upload(new_up, fc.list_sheets(new_up)[0] if fc.list_sheets(new_up) else None) if new_up else None
                with st.spinner(f"Training {model_name}..."):
                    res = fc.run_tabular(df, target, features, model_name, params,
                                         "chronological" if chrono else "random", time_col, test_size, new_df)
                res["settings"] = {"Model": model_name, "Target": target, "Predictors": ", ".join(features),
                                   "Validation": "Chronological hold-out" if chrono else "Random hold-out",
                                   "Held-out share": test_size, **{f"Setting: {k}": v for k, v in params.items()}}
                st.session_state["fc_result"] = res
            except Exception as e:
                st.session_state.pop("fc_result", None)
                st.error(f"Analysis stopped: {e}")

    # ------------------------------------------------------------- results
    res = st.session_state.get("fc_result")
    if res:
        st.divider()
        st.subheader(f"Results: {res['model']}")
        st.caption(f"Fitted on {res['n_train']} rows and validated on {res['n_test']} rows the model did not see."
                   + (f" {res['dropped']} rows with missing values were left out." if res.get("dropped") else ""))

        mt = pd.DataFrame({"Training": res["train_metrics"], "Validation": res["test_metrics"]}).T
        st.dataframe(mt.style.format("{:.3f}"), use_container_width=True)
        gap = res["train_metrics"]["R²"] - res["test_metrics"]["R²"]
        if gap > 0.25:
            note("Training R² is much higher than validation R². The model may be overfitting, so trust the validation figures.")
        if res["test_metrics"]["R²"] < 0:
            note("Validation R² is below zero, meaning the model predicts worse than simply using the average. "
                 "Try other predictors, a simpler model or more data.")

        tt = res["test_table"]
        if res["kind"] == "tabular":
            lo, hi = float(min(tt["Actual"].min(), tt["Predicted"].min())), float(max(tt["Actual"].max(), tt["Predicted"].max()))
            fig = px.scatter(tt, x="Actual", y="Predicted", title="Actual vs predicted (validation rows)")
            fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Perfect fit", line=dict(dash="dash")))
        else:
            h = res["history"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=h["Period"], y=h["Value"], name="Observed", mode="lines+markers"))
            fig.add_trace(go.Scatter(x=tt["Period"], y=tt["Predicted"], name="Validation forecast", mode="lines+markers"))
            f = res["forecast"]
            fig.add_trace(go.Scatter(x=f["Period"], y=f["Upper 95%"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=f["Period"], y=f["Lower 95%"], fill="tonexty", line=dict(width=0),
                                     name="95% interval", fillcolor="rgba(27,127,121,0.2)"))
            fig.add_trace(go.Scatter(x=f["Period"], y=f["Forecast"], name="Forecast", mode="lines+markers"))
            fig.update_layout(title="Observed, validation and future forecast")
        st.plotly_chart(fig, use_container_width=True)

        xcol = "Predicted"
        rfig = px.scatter(tt, x=xcol, y="Residual", title="Residuals (actual minus predicted)")
        rfig.add_hline(y=0, line_dash="dash")
        st.plotly_chart(rfig, use_container_width=True)

        if res.get("importance") is not None:
            top = res["importance"].head(15).iloc[::-1]
            st.plotly_chart(px.bar(top, x="Importance", y="Feature", orientation="h",
                                   title=f"Feature importance ({res['importance_method']})"), use_container_width=True)

        if res["kind"] == "arima":
            st.markdown("**Forecast**")
            st.dataframe(res["forecast"], use_container_width=True)
        elif res.get("new_predictions") is not None:
            st.markdown("**Predictions for your new rows**")
            st.dataframe(res["new_predictions"], use_container_width=True)

        sheets_out = {
            "Settings": pd.DataFrame({"Item": list(res["settings"].keys()), "Value": [str(v) for v in res["settings"].values()]}),
            "Metrics": mt.reset_index(names="Dataset"),
            "Validation predictions": tt,
            "Feature importance": res.get("importance"),
            "Forecast": res.get("forecast"),
            "New predictions": res.get("new_predictions"),
        }
        st.download_button("Download Excel report", fc.build_excel(sheets_out),
                           file_name=f"agrilab_{res['model'].replace(' ', '_').replace('/', '')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
