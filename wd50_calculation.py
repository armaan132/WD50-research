import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("home.csv", skiprows=10)

df.rename(columns={'Date': 'date', 'ppt (inches)': 'ppt'}, inplace=True)

df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

def calculate_wd50_for_year(year_df):
    sorted_daily = year_df['ppt'].sort_values(ascending=False)
    cumulative = sorted_daily.cumsum()
    half_total = sorted_daily.sum() / 2
    wd50 = (cumulative < half_total).sum() + 1
    return wd50

wd50_by_year = df.groupby('year', group_keys=False).apply(calculate_wd50_for_year)

print(wd50_by_year)

wd50_by_year.plot(marker='o', title='WD50 per Year (1990–2017)')
plt.xlabel("Year")
plt.ylabel("WD50 (days)")
plt.grid(True)
plt.tight_layout()
plt.show()
