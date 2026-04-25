import os
import sys
import wx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import seaborn as sns
from datetime import datetime
import pingouin as pg


def Anova_test(data: pd.DataFrame, group_name: str, val_name: str):
    model = ols(f"{val_name} ~ C({group_name})", data=data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    residus = model.resid
    row = [idx for idx in anova_table.index if group_name in idx.lower()]
    if not row:
        raise KeyError(f"Aucune ligne dans anova_table ne correspond à '{group_name}'")
    ss_inter = anova_table.loc[row[0], "sum_sq"]
    df_inter = anova_table.loc[row[0], "df"]
    ms_inter = ss_inter / df_inter
    cm_resid = anova_table.loc["Residual", "mean_sq"] if "mean_sq" in anova_table.columns else anova_table.loc["Residual", "sum_sq"] / anova_table.loc["Residual", "df"]
    n_per_group = 5
    ms_intra = cm_resid
    if ms_inter > ms_intra:
        u_inter = np.sqrt((ms_inter - ms_intra) / n_per_group)
    else:
        u_inter = 0
    u_intra = np.sqrt(ms_intra)
   
    u_total = np.sqrt(u_intra**2 + u_inter**2)
    y_mean = data[val_name].mean()
    u_rel = u_total / y_mean
    # en pourcentage
    u_rel_percent = 100 * u_rel
    return anova_table, residus, u_total, u_rel_percent

def histo(residus, output_manager=None, save_output=False, output_path=None, bins=20): 
    if save_output and not output_path:
        raise ValueError("output_path must be spécifié si save_output est True.")
    plt.figure(figsize=(8, 6))
    plt.hist(residus, bins=bins, color='skyblue', edgecolor='black')
    plt.title("Histogramme des résidus (ANOVA)")
    plt.xlabel("Résidus ANOVA")
    plt.ylabel("Fréquence")
    plt.grid(True)
    if save_output:
        path = f"{output_path}_histogram.png"
        plt.savefig(path, dpi=300, bbox_inches='tight')
        if output_manager:
            output_manager.print_info(f"📊 Histogramme sauvegardé : {path}")
    plt.show(block=False)
    plt.pause(5)
    plt.close()

def Boxplot(data, val_name, group_name, output_manager=None, save_output=False, output_path=None):# oui residus
    plt.figure(figsize=(8, 6))
    if isinstance(val_name, str):
        sns.boxplot(x=data[group_name], y=data[val_name], palette="Set2")
        plt.ylabel(f"Valeurs de {val_name}")
        path = f"{output_path}_boxplot_{val_name}.png"
    else:
        df = pd.DataFrame({"group": data[group_name], "residu": val_name})
        sns.boxplot(x="group", y="residu", data=df, palette="Set2")
        plt.ylabel("Résidus")
        path = f"{output_path}_boxplot_residus.png"
    plt.xlabel("Groupes")
    plt.grid(True)
    if save_output and output_path:
        plt.savefig(path, dpi=300, bbox_inches='tight')
        if output_manager:
            output_manager.print_info(f"📦 Boxplot sauvegardé : {path}")
    plt.show(block=False)
    plt.pause(5)
    plt.close()

def dotplot(data, val_name, group_name, output_manager=None, save_output=False, output_path=None): # nope
    plt.figure(figsize=(8, 6))
    if isinstance(val_name, str):
        sns.stripplot(x=group_name, y=val_name, data=data, jitter=True, palette="Set2")
        plt.ylabel(f"Valeurs de {val_name}")
        path = f"{output_path}_dotplot_{val_name}.png"
    else:
        df = pd.DataFrame({"group": data[group_name], "residu": val_name})
        sns.stripplot(x="group", y="residu", data=df, jitter=True, palette="Set2")
        plt.ylabel("Résidus")
        path = f"{output_path}_dotplot_residus.png"
    plt.xlabel("Groupes")
    plt.title("Dotplot")
    plt.grid(True)
    if save_output and output_path:
        plt.savefig(path, dpi=300, bbox_inches='tight')
        if output_manager:
            output_manager.print_info(f"🎯 Dotplot sauvegardé : {path}")
    plt.show(block=False)
    plt.pause(5)
    plt.close()

def violinplot(data, val_name, group_name, output_manager=None, save_output=False, output_path=None): # oui  residus
    plt.figure(figsize=(8, 6))
    if isinstance(val_name, str):
        sns.violinplot(x=group_name, y=val_name, data=data, palette="Set2")
        path = f"{output_path}_violinplot_{val_name}.png"
    else:
        df = pd.DataFrame({"group": data[group_name], "residu": val_name})
        sns.violinplot(x="group", y="residu", data=df, palette="Set2")
        path = f"{output_path}_violinplot_residus.png"
    plt.xlabel("Groupes")
    plt.ylabel("Valeurs")
    plt.title("Violinplot")
    plt.grid(True)
    if save_output and output_path:
        plt.savefig(path, dpi=300, bbox_inches='tight')
        if output_manager:
            output_manager.print_info(f"🎻 Violinplot sauvegardé : {path}")
    plt.show(block=False)
    plt.pause(5)
    plt.close()

def qqplot_residuals_anova(data, group_name, val_name, by_group=False, Save=None, output_manager=None): # oui
    model = ols(f"{val_name} ~ C({group_name})", data=data).fit()
    residuals = model.resid
    if not by_group:
        fig = pg.qqplot(residuals, dist="norm", confidence=0.95, alpha=0.7, color="blue")
        plt.title("Q-Q plot global des résidus")
        if Save:
            path = f"{Save}qqplot_global.png"
            plt.savefig(path, dpi=300, bbox_inches='tight')
            if output_manager:
                output_manager.print_info(f"📐 Q-Q plot global sauvegardé : {path}")
        plt.show(block=False)
    else:
        data = data.copy()
    data["residu"] = residuals
    groupes = data[group_name].unique()
    n = len(groupes)

    # Grille carrée ou presque pour les subplots
    n_cols = 3
    n_rows = int(np.ceil(n / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
    axes = axes.flatten()

    # Définir la même plage pour tous les axes (même échelle)
    xlim = (-2.5, 2.5)
    ylim = (-2.5, 2.5)

    for i, group in enumerate(groupes):
        resid = data[data[group_name] == group]["residu"]
        ax = axes[i]
        pg.qqplot(resid, dist="norm", confidence=0.95, ax=ax, alpha=0.6, color="blue")
        ax.set_title(f"Q-Q plot – {group}")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.grid(True)

    # Supprimer les axes vides s'il y a moins de subplots que de cases
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # Titre général
    fig.suptitle("Q-Q plots des résidus par groupe", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Sauvegarde
    if Save:
        path = os.path.join(Save, "qqplot_groupes.png")
        plt.savefig(path, dpi=300)
        if output_manager:
            output_manager.print_info(f"📐 Q-Q plots par groupe sauvegardés : {path}")

    plt.show(block=False)
    plt.pause(5)
    plt.close()


def anova_normal(data, group_name, val_name, save_output, output_path=None, output=None):
    anova_table, residus, incertitude, inc_rel = Anova_test(data, group_name, val_name)
    if output:
        output.print_info("📊 ANOVA préliminaire :")
        output.print_info(anova_table)

    qqplot_residuals_anova(data, group_name, val_name, by_group=False, Save=output_path, output_manager=output)
    qqplot_residuals_anova(data, group_name, val_name, by_group=True, Save=output_path, output_manager=output)

    stat_shapiro, p_shapiro = stats.shapiro(residus)
    stat_beran, p_bera = stats.jarque_bera(residus)

    if output:
        output.print_info(f"📈 Test Shapiro-Wilk : p = {p_shapiro:.4f}")
        output.print_info(f"📈 Test Jarque-Bera : p = {p_bera:.4f}")

    Boxplot(data, val_name, group_name, output_manager=output, save_output=save_output, output_path=output_path)
    dotplot(data, val_name, group_name, output_manager=output, save_output=save_output, output_path=output_path)
    violinplot(data, val_name, group_name, output_manager=output, save_output=save_output, output_path=output_path)

    groupes = [data[data[group_name] == g][val_name] for g in data[group_name].unique()]
    stat_levene, p_levene_data = stats.levene(*groupes)
    if output:
        output.print_info(f"📏 Levene (données) : p = {p_levene_data:.4f}")

    data_resid = data.assign(residuals=residus)
    Boxplot(data_resid, "residuals", group_name, output_manager=output, save_output=save_output, output_path=output_path)
    dotplot(data_resid, "residuals", group_name, output_manager=output, save_output=save_output, output_path=output_path)
    violinplot(data_resid, "residuals", group_name, output_manager=output, save_output=save_output, output_path=output_path)

    residus_groupes = [residus[data[group_name] == g] for g in data[group_name].unique()]
    _, p_levene_res = stats.levene(*residus_groupes)
    if output:
        output.print_info(f"📏 Levene (résidus) : p = {p_levene_res:.4f}")
        output.print_info(f"📉 Incertitude estimée : {incertitude}")
        output.print_info(f"📉 Incertitude relative : {inc_rel}")


    return p_shapiro, min(p_levene_data, p_levene_res)

def anova_param(data, group_name, val_name, p_normal, p_homo, save_output=False, output_path=None, output=None):
    groupes = [data[data[group_name] == g][val_name] for g in data[group_name].unique()]
    p_normal = float(p_normal)
    p_homo = float(p_homo)

    if p_normal > 0.05 and p_homo > 0.05:
        model = ols(f"{val_name} ~ C({group_name})", data=data).fit()
        anova_results = sm.stats.anova_lm(model, typ=2)
        if output:
            output.print_info("✅ ANOVA paramétrique :")
            output.print_info(anova_results)
        if save_output and output_path:
            with open(output_path, "a", encoding="utf-8") as f:
                f.write("ANOVA paramétrique :\n")
                f.write(str(anova_results) + "\n\n")
        return anova_results
    else:
        stat_kruskal, p_kruskal = stats.kruskal(*groupes)
        if output:
            output.print_info("✅ ANOVA non paramétrique (Kruskal-Wallis) :")
            output.print_info(f"Statistique de test : {stat_kruskal:.4f}")
            output.print_info(f"Valeur p : {p_kruskal:.4f}")
        if save_output and output_path:
            with open(output_path, "a", encoding="utf-8") as f:
                f.write("ANOVA non paramétrique (Kruskal-Wallis) :\n")
                f.write(f"Statistique de test : {stat_kruskal:.4f}\n")
                f.write(f"Valeur p : {p_kruskal:.4f}\n\n")
        return stat_kruskal, p_kruskal
