import numpy as np
from sklearn.linear_model import LinearRegression

# Load data from csv file
data = np.loadtxt("data/training_data.csv", delimiter=",")

# Input values; first two columns
X = data[:, 0:2]

# Output values; last column
Y = data[:, 2]

# Create linear regression model
model = LinearRegression().fit(X, Y)

# Print score
print(f"Model score: {model.score(X, Y)}")

# Print the model parameters
print("Model parameters:")
print(f"  - Coefficients: {model.coef_}")
print(f"  - Intercept: {model.intercept_}")