
# from scipy.stats import ttest_rel, wilcoxon, shapiro
#
# # Run paired t-tests: MinMo > NoMinMo (with normality check)
# ttest_results = []
#
# for movement in movements:
#     for roi in movement_roi_map[movement]:
#         for hemi in hemis:
#             minmo_betas = df_b_t_values_rois[(df_b_t_values_rois["condition"] == "MinMo") &
#                                         (df_b_t_values_rois["ROI"] == roi) &
#                                         (df_b_t_values_rois["movement"] == movement) &
#                                         (df_b_t_values_rois["hemi"] == hemi)]
#
#             nominmo_betas = df_b_t_values_rois[(df_b_t_values_rois["condition"] == "NoMinMo") &
#                                           (df_b_t_values_rois["ROI"] == roi) &
#                                           (df_b_t_values_rois["movement"] == movement) &
#                                           (df_b_t_values_rois["hemi"] == hemi)]
#
#             common_subjects = set(minmo_betas["subject"]).intersection(set(nominmo_betas["subject"]))
#             minmo_betas = minmo_betas[minmo_betas["subject"].isin(common_subjects)].sort_values("subject")
#             nominmo_betas = nominmo_betas[nominmo_betas["subject"].isin(common_subjects)].sort_values("subject")
#
#             if len(common_subjects) > 1:
#                 minmo_vals = minmo_betas["beta_coef"].values
#                 nominmo_vals = nominmo_betas["beta_coef"].values
#
#                 # Normality check
#                 _, p_norm_minmo = shapiro(minmo_vals)
#                 _, p_norm_nominmo = shapiro(nominmo_vals)
#
#                 if p_norm_minmo > 0.05 and p_norm_nominmo > 0.05:
#                     # Both distributions are normal → t-test
#                     t_stat, p_val = ttest_rel(minmo_vals, nominmo_vals, alternative='greater')
#                     test_type = "ttest"
#                 else:
#                     # Non-normal → Wilcoxon signed-rank test
#                     try:
#                         t_stat, p_val = wilcoxon(minmo_vals, nominmo_vals, alternative='greater')
#                         test_type = "wilcoxon"
#                     except ValueError:
#                         t_stat, p_val = np.nan, np.nan
#                         test_type = "wilcoxon_failed"
#
#                 ttest_results.append({
#                     "movement": movement,
#                     "ROI": roi,
#                     "hemi": hemi,
#                     "t_stat": t_stat,
#                     "p_val": p_val,
#                     "test": test_type,
#                     "n_subjects": len(common_subjects),
#                     "shapiro_minmo_p": p_norm_minmo,
#                     "shapiro_nominmo_p": p_norm_nominmo
#                 })
#
#
# # Compile and correct p-values
# df_ttest_results = pd.DataFrame(ttest_results)
# df_ttest_results["p_val_fdr"] = smm.multipletests(df_ttest_results["p_val"], method="fdr_bh")[1]
# df_ttest_results["significant"] = df_ttest_results["p_val_fdr"] < 0.01
# df_ttest_results.to_csv(group_analysis_dir / 'df_ttest_results_rois_by_movement.csv', index=False)
#
#
# # Plotting: beta weight distributions
# plot_dir = deriv_fldr / 'group_analysis' / 'plots_beta_distributions'
# plot_dir.mkdir(parents=True, exist_ok=True)
#
# # Iterate over combinations of movement, ROI, and hemisphere
# for movement in df_b_t_values_rois['movement'].unique():
#     for roi in df_b_t_values_rois['ROI'].unique():
#         for hemi in df_b_t_values_rois['hemi'].unique():
#             df_plot = df_b_t_values_rois[
#                 (df_b_t_values_rois['movement'] == movement) &
#                 (df_b_t_values_rois['ROI'] == roi) &
#                 (df_b_t_values_rois['hemi'] == hemi)
#             ]
#             if df_plot.empty:
#                 continue
#
#             plt.figure(figsize=(6, 4))
#             sns.violinplot(
#                 data=df_plot,
#                 x='condition',
#                 y='beta_coef',
#                 inner='box',
#                 palette='Set2'
#             )
#             sns.stripplot(
#                 data=df_plot,
#                 x='condition',
#                 y='beta_coef',
#                 color='black',
#                 alpha=0.5,
#                 jitter=True,
#                 size=3
#             )
#             plt.title(f"{movement} | {roi} | {hemi}")
#             plt.ylabel('Beta Coefficient')
#             plt.tight_layout()
#             outname = f"{movement}_{roi}_{hemi}.png".replace("/", "-")
#             plt.savefig(plot_dir / outname)
#             plt.close()
