import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def read_csv_and_process(filename):
    df = pd.read_csv(filename)
    
    # Convert the state columns from string to list of floats
    state_in = df['state_in'].apply(lambda x: [float(i) for i in x.strip("[]").split(", ")]).tolist()
    state_pred = df['state_pred'].apply(lambda x: [float(i) for i in x.strip("[]").split(", ")]).tolist()
    state_out = df['state_out'].apply(lambda x: [float(i) for i in x.strip("[]").split(", ")]).tolist()
    
    return np.array(state_in), np.array(state_pred), np.array(state_out), df['timestamp'].values

def compute_rmse(error):
    return np.sqrt(np.mean(error**2))

# Read and process data
path = os.environ['AGI_PATH'] + "/externals/data_driven_mpc/ros_gp_mpc/data"
state_in1, state_pred1, state_out1, timestamp1 = read_csv_and_process(os.path.join(path,'dataset_001_bem_simple.csv'))
state_in2, state_pred2, state_out2, timestamp2 = read_csv_and_process(os.path.join(path,'dataset_001_bem_simple_2.csv'))
state_in3, state_pred3, state_out3, timestamp3 = read_csv_and_process(os.path.join(path,'dataset_001_bem_simple_3.csv'))

# Compute errors
error1 = state_out1 - state_pred1
error2 = state_out2 - state_pred2
error3 = state_out3 - state_pred3

# Plot error for each dimension
for i in range(13):
    plt.figure(figsize=(10, 5))
    
    rmse1 = compute_rmse(error1[:, i])
    rmse2 = compute_rmse(error2[:, i])
    rmse3 = compute_rmse(error3[:, i])
    
    plt.plot(timestamp1, error1[:, i], label=f'File1 Error (RMSE: {rmse1:.4f})')
    plt.plot(timestamp2, error2[:, i], label=f'File2 Error (RMSE: {rmse2:.4f})')
    plt.plot(timestamp3, error3[:, i], label=f'File3 Error (RMSE: {rmse3:.4f})')
    
    plt.xlabel('Timestamp')
    plt.ylabel(f'Error in Dimension {i}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(path,f"err_{i}.png"))
    plt.close()
