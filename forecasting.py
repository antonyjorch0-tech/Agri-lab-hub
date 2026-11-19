"""Forecasting engine for AgriLab Hub.

Every metric is computed on genuinely held-out data. Nothing here tunes results
to reach a target R² - the numbers you see are the numbers the model earned.
"""
import io
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor

# (name, family, available now?)
CATALOG = [
    ("XGBoost", "Gradient boosting", True),
    ("LightGBM", "Gradient boosting", False),
    ("CatBoost", "Gradient boosting", False),
    ("Random Forest", "Ensemble learning", True),
    ("ANN / MLP", "Artificial neural network", True),
    ("Support Vector Regression", "Kernel learning", True),
    ("LSTM", "Deep learning", False),
    ("GRU", "Deep learning", False),
    ("CNN-LSTM", "Deep learning", False),
    ("ARIMA", "Time series", True),
    ("SARIMA", "Seasonal time series", False),
    ("Exponential Smoothing", "Time series", False),
    ("Prophet", "Time series", False),
    ("Linear Regression", "Statistical learning", True),
    ("Ridge / Lasso", "Regularized regression", False),
    ("K-Nearest Neighbors", "Machine learning", True),
    ("Gradient Boosting", "Ensemble learning", True),
    ("Extra Trees", "Ensemble learning", True),
]


def available_models():
    return [n for n, _, ok in CATALOG if ok]


# ---------------------------------------------------------------- data input
def list_sheets(file):
    if str(file.name).lower().endswith((".xlsx", ".xls")):
        file.seek(0)
        return pd.ExcelFile(file).sheet_names
    return []


def read_upload(file, sheet=None) -> pd.DataFrame:
    file.seek(0)
    if str(file.name).lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file, sheet_name=sheet or 0)
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)


# ------------------------------------------------------------------- metrics
def metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    nz = y_true != 0
    mape = float(np.mean(np.abs((y_true[nz] - y_pred[nz]) / y_true[nz])) * 100) if nz.any() else np.nan
    return {
        "R²": float(r2_score(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "MAPE (%)": mape,
    }


# -------------------------------------------------------------------- models
def make_model(name: str, p: dict):
    if name == "XGBoost":
        return XGBRegressor(n_estimators=p.get("n_estimators", 300), max_depth=p.get("max_depth", 3),
                            learning_rate=p.get("learning_rate", 0.1), subsample=0.9,
                            random_state=42, n_jobs=1, verbosity=0)
    if name == "Random Forest":
        return RandomForestRegressor(n_estimators=p.get("n_estimators", 300), max_depth=p.get("max_depth"),
                                     random_state=42, n_jobs=1)
    if name == "Extra Trees":
        return ExtraTreesRegressor(n_estimators=p.get("n_estimators", 300), max_depth=p.get("max_depth"),
                                   random_state=42, n_jobs=1)
    if name == "Gradient Boosting":
        return GradientBoostingRegressor(n_estimators=p.get("n_estimators", 200), max_depth=p.get("max_depth", 3),
                                         learning_rate=p.get("learning_rate", 0.1), random_state=42)
    if name == "Support Vector Regression":
        return TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(), SVR(kernel=p.get("kernel", "rbf"), C=p.get("C", 1.0),
                                                          epsilon=p.get("epsilon", 0.1))),
            transformer=StandardScaler())
    if name == "ANN / MLP":
        h = p.get("hidden", 32)
        return TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(h, h), alpha=p.get("alpha", 0.001),
                                                                   max_iter=p.get("max_iter", 2000), random_state=42)),
            transformer=StandardScaler())
    if name == "K-Nearest Neighbors":
        return TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=p.get("k", 5))),
            transformer=StandardScaler())
    if name == "Linear Regression":
        return make_pipeline(StandardScaler(), LinearRegression())
    raise ValueError(f"{name} is not available yet.")


def _importance(model, X_test, y_test):
    imp = getattr(model, "feature_importances_", None)
    if imp is not None:
        return pd.DataFrame({"Feature": X_test.columns, "Importance": imp}).sort_values("Importance", ascending=False), "Built-in importance"
    if len(X_test) >= 5:
        pi = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
        df = pd.DataFrame({"Feature": X_test.columns, "Importance": pi.importances_mean})
        return df.sort_values("Importance", ascending=False), "Permutation importance on validation data"
    return None, ""


def run_tabular(df, target, features, model_name, params, split="chronological",
                time_col=None, test_size=0.2, new_df=None) -> dict:
    if not features:
        raise ValueError("Select at least one predictor variable.")
    cols = list(dict.fromkeys([target] + list(features) + ([time_col] if split == "chronological" and time_col else [])))
    work = df[cols].copy()
    work[target] = pd.to_numeric(work[target], errors="coerce")
    n_before = len(work)
    work = work.dropna().reset_index(drop=True)
    dropped = n_before - len(work)
    if len(work) < 15:
        raise ValueError(f"Only {len(work)} complete rows remain after removing missing values. At least 15 are needed.")

    X_all = pd.get_dummies(work[list(features)], dtype=float)
    y_all = work[target].astype(float)

    if split == "chronological":
        order = work.sort_values(time_col, kind="stable").index
        n_test = max(3, int(round(len(work) * test_size)))
        train_idx, test_idx = order[:-n_test], order[-n_test:]
    else:
        train_idx, test_idx = train_test_split(work.index, test_size=test_size, random_state=42)

    X_tr, X_te = X_all.loc[train_idx], X_all.loc[test_idx]
    y_tr, y_te = y_all.loc[train_idx], y_all.loc[test_idx]

    model = make_model(model_name, params)
    model.fit(X_tr, y_tr)
    p_tr, p_te = model.predict(X_tr), model.predict(X_te)

    test_out = work.loc[test_idx, cols].copy()
    test_out["Actual"], test_out["Predicted"] = y_te.values, p_te
    test_out["Residual"] = test_out["Actual"] - test_out["Predicted"]

    imp, imp_method = _importance(model, X_te, y_te)

    new_pred = None
    if new_df is not None:
        missing = [c for c in features if c not in new_df.columns]
        if missing:
            raise ValueError(f"The new-data file is missing these predictor columns: {', '.join(missing)}")
        nd = new_df.copy()
        if nd[list(features)].isna().any().any():
            raise ValueError("The new-data file has empty cells in the predictor columns. Fill or remove them first.")
        X_new = pd.get_dummies(nd[list(features)], dtype=float).reindex(columns=X_all.columns, fill_value=0.0)
        final = clone(model).fit(X_all, y_all)  # refit on all data for predicting new rows
        new_pred = nd.copy()
        new_pred[f"Predicted {target}"] = final.predict(X_new)

    return {
        "kind": "tabular", "model": model_name, "target": target, "features": list(features),
        "split": split, "n_train": len(train_idx), "n_test": len(test_idx), "dropped": dropped,
        "train_metrics": metrics(y_tr, p_tr), "test_metrics": metrics(y_te, p_te),
        "test_table": test_out.reset_index(drop=True), "importance": imp, "importance_method": imp_method,
        "new_predictions": new_pred, "params": params,
    }


def _future_labels(labels, h):
    labels = pd.Index(labels)
    if pd.api.types.is_integer_dtype(labels):
        return [int(labels[-1]) + i for i in range(1, h + 1)]
    if pd.api.types.is_datetime64_any_dtype(labels):
        freq = pd.infer_freq(labels) if len(labels) >= 3 else None
        if freq:
            return list(pd.date_range(labels[-1], periods=h + 1, freq=freq)[1:])
        step = pd.Series(labels).diff().median()
        return [labels[-1] + step * i for i in range(1, h + 1)]
    return [f"t+{i}" for i in range(1, h + 1)]


def run_arima(series: pd.Series, order, n_test: int, horizon: int) -> dict:
    from statsmodels.tsa.arima.model import ARIMA

    y = pd.to_numeric(series, errors="coerce").dropna()
    if len(y) < 10:
        raise ValueError(f"The series has only {len(y)} points. ARIMA needs at least 10.")
    if n_test < 2 or n_test >= len(y) - 5:
        raise ValueError("Choose a validation length of at least 2 points that leaves 6 or more points for fitting.")
    labels, vals = y.index, y.values.astype(float)
    train, test = vals[:-n_test], vals[-n_test:]
    d = order[1]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ARIMA(train, order=order).fit()
        pred = np.asarray(fit.forecast(n_test))
        fitted = np.asarray(fit.fittedvalues)
        full = ARIMA(vals, order=order).fit()
        fc = full.get_forecast(horizon)
        mean = np.asarray(fc.predicted_mean)
        ci = np.asarray(fc.conf_int(alpha=0.05))

    test_table = pd.DataFrame({"Period": labels[-n_test:], "Actual": test, "Predicted": pred})
    test_table["Residual"] = test_table["Actual"] - test_table["Predicted"]
    forecast = pd.DataFrame({"Period": _future_labels(labels, horizon), "Forecast": mean,
                             "Lower 95%": ci[:, 0], "Upper 95%": ci[:, 1]})
    return {
        "kind": "arima", "model": "ARIMA", "order": tuple(order), "n_train": len(train), "n_test": n_test,
        "train_metrics": metrics(train[d:], fitted[d:]), "test_metrics": metrics(test, pred),
        "test_table": test_table, "forecast": forecast,
        "history": pd.DataFrame({"Period": labels, "Value": vals}),
        "aic": float(fit.aic), "importance": None,
    }


def build_excel(sheets: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            if frame is not None:
                frame.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()
