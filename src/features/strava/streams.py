import httpx
import base64
import plotly.graph_objects as go
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
        "keys": "time,heartrate,velocity_smooth",
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
        
    # Convert time from seconds to minutes for cleaner X axis
    x_axis_min = [t / 60 for t in time_series]

    # Create figure with secondary Y-axis
    # Note: we use make_subplots or just direct layout configuring for dual axis
    fig = go.Figure()

    # Add Pace Trace
    fig.add_trace(go.Scatter(
        x=x_axis_min,
        y=pace_series,
        name="Pace (min/km)",
        mode='lines',
        line=dict(color="#58A4B0", width=1.5),
        yaxis="y1"
    ))

    # Add Heart Rate Trace
    fig.add_trace(go.Scatter(
        x=x_axis_min,
        y=hr_series,
        name="Heart Rate (BPM)",
        mode='lines',
        line=dict(color="#D64933", width=1.5),
        yaxis="y2"
    ))

    # Apply runrun.rest UI Theme
    fig.update_layout(
        paper_bgcolor="#0C0F0A",
        plot_bgcolor="#0C0F0A",
        font=dict(color="#BAC1B8", family="sans-serif", size=12),
        title=dict(text="Workout Telemetry", font=dict(color="#BAC1B8", size=16)),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            title="Time (minutes)",
            showgrid=True,
            gridcolor="#242325",
            zerolinecolor="#242325",
        ),
        yaxis=dict(
            title="Pace",
            showgrid=True,
            gridcolor="#242325",
            zerolinecolor="#242325",
            autorange="reversed", # Faster pace (lower value) is higher on graph
            tickformat=".1f",     # e.g., 5.5 min/km
            side="left"
        ),
        yaxis2=dict(
            title="Heart Rate (BPM)",
            showgrid=False,
            zerolinecolor="#242325",
            side="right",
            overlaying="y"
        )
    )

    # Export to PNG via kaleido
    img_bytes = fig.to_image(format="png", engine="kaleido", width=800, height=450)
    
    # Encode as Base64
    b64_str = base64.b64encode(img_bytes).decode("utf-8")
    return b64_str
