import httpx
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.features.strava.auth import get_valid_strava_token
from src.shared.logger import logger

async def fetch_activity_streams(activity_id: int, user_id: str) -> dict | None:
    """
    Fetches raw high-resolution stream data (time, HR, pace) for a specific workout.
    Returns a dictionary of streams mapped by type, or None if failed.
    """
    token = await get_valid_strava_token(user_id)
    if not token:
        logger.error(f"Cannot fetch streams: no valid Strava token for user {user_id}")
        return None

    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    params = {
        "keys": "time,heartrate,velocity_smooth,altitude",
        "key_by_type": "true"
    }
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"404 Activity {activity_id} not found or missing streams.")
                return {"error": "Activity missing telemetry data or manually entered."}
            logger.error(f"HTTP error fetching streams for activity {activity_id}: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching streams for activity {activity_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching streams for activity {activity_id}: {e}")
            return None

def generate_stream_chart_base64(streams: dict) -> str:
    """
    Takes a Strava streams dictionary (key_by_type=true) and generates a Plotly chart
    of Pace vs Heart Rate over distance or time. Returns a Base64-encoded PNG image string.
    """
    if "time" not in streams:
        raise ValueError("Streams data is missing 'time' key")
        
    time_series = streams["time"]["data"]  # X-axis (seconds)
    
    # Process Pace (from velocity_smooth in m/s)
    pace_series = []
    if "velocity_smooth" in streams:
        for v in streams["velocity_smooth"]["data"]:
            if v and v > 0:
                pace = 16.6666667 / v  # 1000 / (v * 60)
                # Cap pace at 15 min/km (walking very slowly) to avoid huge spikes when stopped
                pace_series.append(min(pace, 15.0))
            else:
                pace_series.append(15.0) # substitute stopped with 15 min/km
    else:
        # Default empty array if no pace
        pace_series = [None] * len(time_series)

    # Process Heart Rate
    hr_series = []
    if "heartrate" in streams:
        hr_series = streams["heartrate"]["data"]
    else:
        hr_series = [None] * len(time_series)
        
    # Process Altitude
    alt_series = []
    if "altitude" in streams:
        alt_series = streams["altitude"]["data"]
    else:
        alt_series = [None] * len(time_series)
        
    # Convert time from seconds to minutes for cleaner X axis
    x_axis_min = [t / 60 for t in time_series]

    # Create figure with 2 rows for Subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )

    # Add Pace Trace
    fig.add_trace(go.Scatter(
        x=x_axis_min,
        y=pace_series,
        name="Pace",
        mode='lines',
        line=dict(color="#58A4B0", width=1.5),
    ), row=1, col=1, secondary_y=False)

    # Add Heart Rate Trace
    fig.add_trace(go.Scatter(
        x=x_axis_min,
        y=hr_series,
        name="Heart Rate",
        mode='lines',
        line=dict(color="#D64933", width=1.5),
    ), row=1, col=1, secondary_y=True)

    # Add Altitude Trace
    fig.add_trace(go.Scatter(
        x=x_axis_min,
        y=alt_series,
        name="Altitude",
        mode='lines',
        line=dict(color="#545b53", width=1),
        fill='tozeroy',
        fillcolor="#242325"
    ), row=2, col=1, secondary_y=False)

    # Apply runrun.rest UI Theme
    fig.update_layout(
        paper_bgcolor="#0C0F0A",
        plot_bgcolor="#0C0F0A",
        font=dict(color="#BAC1B8", family="sans-serif", size=12),
        title=dict(text="Workout Telemetry", font=dict(color="#BAC1B8", size=16)),
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=False
    )

    # Note: make_subplots uses yaxis, yaxis2, yaxis3, xaxis, xaxis2 etc. under the hood.
    # In this configuration:
    # xaxis: X-axis for top subplot (hidden ticks due to shared_xaxes)
    # xaxis2: X-axis for bottom subplot
    # yaxis: Pace (left, top subplot)
    # yaxis2: Heart Rate (right, top subplot, secondary_y=True)
    # yaxis3: Altitude (left, bottom subplot)

    fig.update_xaxes(
        showgrid=True, gridcolor="#242325", zerolinecolor="#242325", 
        row=1, col=1
    )
    fig.update_xaxes(
        title_text="Time (minutes)", showgrid=True, gridcolor="#242325", zerolinecolor="#242325", 
        row=2, col=1
    )

    fig.update_yaxes(
        title_text="Pace (min/km)", showgrid=True, gridcolor="#242325", zerolinecolor="#242325", 
        autorange="reversed", tickformat=".1f", 
        row=1, col=1, secondary_y=False
    )
    fig.update_yaxes(
        title_text="BPM", showgrid=False, zerolinecolor="#242325",
        row=1, col=1, secondary_y=True
    )
    fig.update_yaxes(
        title_text="Elevation", showgrid=True, gridcolor="#242325", zerolinecolor="#242325",
        row=2, col=1, secondary_y=False
    )

    # Export to PNG via kaleido
    img_bytes = fig.to_image(format="png", engine="kaleido", width=800, height=450)
    
    # Encode as Base64
    b64_str = base64.b64encode(img_bytes).decode("utf-8")
    return b64_str
