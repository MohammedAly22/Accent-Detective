from typing import List, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


label_mapping = {
    "us": "American",
    "canada": "Canadian",
    "australia": "Australian",
    "england": "British",
    "indian": "Indian",
}


def create_confidence_bar(confidence: float) -> str:
    """
    Generate a styled HTML snippet for a visual confidence bar.

    Args:
        - confidence (float): The confidence value between 0 and 100.

    Returns:
        - str: HTML code representing the confidence bar with percentage and color coding.
    """
    color = (
        "#28a745" if confidence > 70 else "#ffc107" if confidence > 50 else "#dc3545"
    )

    return f"""
    <div class="confidence-bar">
        <div class="progress-fill" style="width: {confidence}%; background-color: {color};"></div>
    </div>
    <div style="text-align: center; margin-top: 0.5rem; color: {color}; font-size: 25px;">
        {confidence:.2f}% Confidence
    </div>
    """


def create_accents_chart(predicted_scores_accent: List[Dict[str, float]]) -> go.Figure:
    """
    Create a horizontal bar chart displaying accent classification confidence scores.

    Args:
        - predicted_scores_accent (List[Dict[str, float]]):
            A list of dictionaries containing 'label' and 'score' keys
            representing accent predictions and their confidence levels.

    Returns:
        - go.Figure: A Plotly Figure object showing the accent classification results.
    """

    # Apply label mapping
    for item in predicted_scores_accent:
        item["label"] = label_mapping.get(item["label"], item["label"])

    df = pd.DataFrame(predicted_scores_accent)

    # Sort for better visual appearance (optional)
    df = df.sort_values(by="score", ascending=True)

    # Plot with Plotly (horizontal bar + custom colormap)
    fig = px.bar(
        df,
        y="label",
        x="score",
        orientation="h",
        title="Accent Classification Results",
        labels={"label": "Accent", "score": "Confidence"},
        text="score",
        color="label",
        color_discrete_sequence=px.colors.sequential.Viridis,
    )

    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(
        xaxis_tickformat=".0%",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        showlegend=False,
        height=400,
    )

    return fig
