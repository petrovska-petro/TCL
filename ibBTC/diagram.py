import plotly.graph_objects as go

fig = go.Figure(
    data=[
        go.Sankey(
            valueformat=".0f",
            valuesuffix=" CVX",
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=[
                    "Harvest",
                    "Tokens to DAO",
                    "WBTC=0.09375 to ibBTC",
                    "ibBTC=0.15625 to depositors",
                    "Tokens to Depositors",
                ],
                color=[
                    "rgba(31, 119, 180, 0.8)",
                    "rgba(255, 127, 14, 0.8)",
                    "rgba(44, 160, 44, 0.8)",
                    "rgba(214, 39, 40, 0.8)",
                    "rgba(148, 103, 189, 0.8)",
                ],
            ),
            link=dict(
                # all comes from the harvest
                source=[0, 0, 0, 0, 0, 0, 2],
                target=[1, 2, 3, 4, 5],
                value=[2375, 750, 1250, 5250],
            ),
        )
    ]
)

fig.update_layout(
    title_text="Harvest Distribution of 10k CVX", font=dict(size=12, color="#000000")
)
fig.show()
