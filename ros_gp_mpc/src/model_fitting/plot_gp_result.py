import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import joblib
from src.model_fitting.gp_common import restore_gp_regressors, GPDataset, world_to_body_velocity_mapping
from src.utils.utils import v_dot_q, quaternion_inverse, separate_variables, undo_jsonify
from src.config.configuration_parameters import ModelFitConfig as Conf
import os

dir = '/home/flightmare/catkin_ws/src/agilicious_archive/agilib/externals/data/simplified_sim_dataset/train'
file = 'dataset_001.csv'
select_x = 7
x_features = [select_x]
u_features = []
df = pd.read_csv(os.path.join(dir, file))
gp_dataset = GPDataset(df, x_features, u_features, select_x, cap=Conf.velocity_cap, n_bins=Conf.histogram_bins, thresh=Conf.histogram_threshold, visualize_data=False)

x_test = gp_dataset.get_x(pruned=True, raw=True)
x_out = gp_dataset.get_x_out(pruned=True)
u_test = gp_dataset.get_u(pruned=True, raw=True)
y_test = gp_dataset.get_y(pruned=True, raw=False)
dt_test = gp_dataset.get_dt(pruned=True)
x_pred = gp_dataset.get_x_pred(pruned=True, raw=False)

x_vis_feats=x_features
u_vis_feats=u_features
y_vis_feats=select_x
    
# Load gps
loaded_models = []
dir = '/home/flightmare/catkin_ws/src/agilicious_archive/agilib/externals/results/model_fitting/simple_sim_gp'
y_dim = [7, 8, 9]
for y in y_dim:
    file = f'drag__motor_noise__noisy__no_payload_{y}_0.pkl'
    loaded_models.append(joblib.load(os.path.join(dir, file)))

pre_trained_models = {"models": loaded_models}
gp_ensemble = restore_gp_regressors(pre_trained_models)

assert y_dim == list(gp_ensemble.gp.keys())

if gp_ensemble is None:
    raise ValueError("gp ensemble is none")

if isinstance(y_vis_feats, list):
    y_dims = [np.where(gp_ensemble.dim_idx == y_dim)[0][0] for y_dim in y_vis_feats]
else:
    y_dims = np.where(gp_ensemble.dim_idx == y_vis_feats)[0]

#### EVALUATE GP ON TEST SET #### #
print("Test set prediction...")
outs = gp_ensemble.predict(x_test.T, u_test.T, return_std=True, progress_bar=True)

mean_estimate_list = []
std_estimate_list = []
# iterate over all items in outs["pred"] and outs["cov_or_std"]
for pred, std_pred in zip(outs["pred"], outs["cov_or_std"]):
    mean_estimate = np.atleast_2d(pred).T * dt_test[:, np.newaxis]
    mean_estimate_list.append(mean_estimate)
    std_estimate = np.atleast_2d(std_pred).T * dt_test[:, np.newaxis]
    std_estimate_list.append(std_estimate)

mean_estimate_body = np.hstack(mean_estimate_list)  # (785,3)
std_estimate_body = np.hstack(std_estimate_list)  # (785,3)

# Undo dt normalization
y_test *= dt_test[:, np.newaxis]

# Error of nominal model
nominal_diff = y_test

# GP regresses model error, correct the predictions of the nominal model
augmented_diff = nominal_diff - mean_estimate_body[:,y_dims]

nominal_rmse = np.mean(np.abs(nominal_diff), 0)
augmented_rmse = np.mean(np.abs(augmented_diff), 0)

labels = [r'$v_x$ error', r'$v_y$ error', r'$v_z$ error']

x_out_df_world = undo_jsonify(df['state_out'].to_numpy())
x_pred_df_world = undo_jsonify(df['state_pred'].to_numpy())
dt_df = df['dt'].to_numpy()

x_out_df_body = world_to_body_velocity_mapping(x_out_df_world)
x_pred_df_body = world_to_body_velocity_mapping(x_pred_df_world)

t_vec = np.cumsum(dt_test)

# Construct y_err_df_body from y_err_df_world (should be same as mean_estimate_body)
y_err_df_world = x_out_df_world - x_pred_df_world
x_df_world = x_test
_, q, _, _ = separate_variables(x_df_world)
_, _, v_w, _ = separate_variables(y_err_df_world)
v_b = []
for i in range(len(q)):
    v_b.append(v_dot_q(v_w[i], quaternion_inverse(q[i])))
v_b = np.stack(v_b)

y_err_df_body = v_b

# Plot error in body frame
plt.figure()
plt.plot(t_vec, x_out_df_body[1:,select_x]-x_pred_df_body[1:,select_x],'r',label='x_out_df_body-x_pred_df_body')
plt.plot(t_vec, mean_estimate_body[:,y_dims],'k',label='mean_estimate_body')
plt.legend()
plt.tight_layout()
plt.grid(True)
plt.savefig(os.path.join(dir, f'x_mean_body_{select_x}.png'))
plt.close()

# Construct y_err_df_world from mean_estimate_body (this is the other way around as above)
v_b = mean_estimate_body
_, q, _, _ = separate_variables(x_df_world)
v_w = []
for i in range(len(q)):
    v_w.append(v_dot_q(v_b[i], q[i]))  # use the original quaternion q
v_w = np.stack(v_w)

mean_estimate_world = v_w

# Plot error in world frame
plt.figure()
plt.plot(t_vec, x_out_df_world[1:,select_x]-x_pred_df_world[1:,select_x],'r',label='x_out_df_world-x_pred_df_world')
plt.plot(t_vec, mean_estimate_world[:,y_dims],'k',label='mean_estimate_world')
plt.legend()
plt.tight_layout()
plt.grid(True)
plt.savefig(os.path.join(dir, f'x_mean_world_{select_x}.png'))
plt.close()
