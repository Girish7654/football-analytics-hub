import os
import pandas as pd
import streamlit as st
import plotly.express as px
import sqlalchemy
from sqlalchemy import create_engine
from dotenv import load_dotenv
from st_aggrid import AgGrid, GridOptionsBuilder

# Page config and theme
st.set_page_config(page_title="Football Analytics Hub", page_icon="⚽", layout="wide")
st.title("Football Analytics Hub")

# Load environment variables
# load_dotenv()
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_NAME = os.getenv("DB_NAME", "football")
# DB_USER = os.getenv("DB_USER", "postgres")
# DB_PASS = os.getenv("DB_PASSWORD", "password")
# DB_PORT = os.getenv("DB_PORT", "5432")

# # Initialize database connection
# try:
#     engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
#     # Test connection with a simple query
#     engine.connect()
# except Exception as e:
#     st.error(f"Failed to connect to database: {e}")
#     st.stop()


DATABASE_URL = st.secrets["DATABASE_URL"]

try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    engine.connect()
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()





# Sidebar navigation
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to Section:", 
    ["👥 Players", "⚽ Top Scorers", "🤕 Injuries", "💰 Transfers", "🏟️ Club Analysis", "📊 Match Stats"])

# Section 1: Players Explorer
if section == "👥 Players":
    st.subheader("All Players")
    # Query players and club names
    players_query = """
        SELECT p.player_id, p.first_name, p.last_name, c.club_name, p.nationality, p.position, p.market_value
        FROM Players p LEFT JOIN Clubs c ON p.club_id = c.club_id;
    """
    players_df = pd.read_sql(players_query, engine)
    players_df['Player Name'] = players_df['first_name'] + " " + players_df['last_name']
    # Move Player Name to front for convenience
    col_order = ["Player Name", "club_name", "nationality", "position", "market_value"]
    players_df = players_df[col_order]
    players_df.rename(columns={"club_name": "Club", "nationality": "Nationality", 
                               "position": "Position", "market_value": "Market Value (€)"}, inplace=True)
    # Sidebar filters
    club_options = sorted(players_df["Club"].dropna().unique())
    nat_options = sorted(players_df["Nationality"].dropna().unique())
    pos_options = sorted(players_df["Position"].dropna().unique())
    st.sidebar.subheader("Player Filters")
    club_filter = st.sidebar.multiselect("Club", club_options)
    nat_filter = st.sidebar.multiselect("Nationality", nat_options)
    pos_filter = st.sidebar.multiselect("Position", pos_options)
    # Apply filters
    filtered_df = players_df.copy()
    if club_filter:
        filtered_df = filtered_df[filtered_df["Club"].isin(club_filter)]
    if nat_filter:
        filtered_df = filtered_df[filtered_df["Nationality"].isin(nat_filter)]
    if pos_filter:
        filtered_df = filtered_df[filtered_df["Position"].isin(pos_filter)]
    st.write(f"**Total Players:** {filtered_df.shape[0]}")
    # Display player table with AgGrid for interactivity
    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_pagination(enabled=True, paginationAutoPageSize=True)
    gb.configure_default_column(groupable=True, sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(filtered_df, gridOptions=grid_options, theme='alpine', height=400)
    
# Section 2: Top Scorers
elif section == "⚽ Top Scorers":
    st.subheader("Top Goal Scorers")
    # Query top scorers (aggregate goals by player)
    top_scorers_query = """
        SELECT p.first_name, p.last_name, SUM(s.goals) as total_goals
        FROM Player_Stats s
        JOIN Players p ON s.player_id = p.player_id
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_goals DESC
        LIMIT 10;
    """
    top_scorers_df = pd.read_sql(top_scorers_query, engine)
    top_scorers_df["Player"] = top_scorers_df["first_name"] + " " + top_scorers_df["last_name"]
    top_scorers_df = top_scorers_df[["Player", "total_goals"]]
    top_scorers_df.rename(columns={"total_goals": "Goals"}, inplace=True)
    # Display table
    st.dataframe(top_scorers_df, use_container_width=True)
    # Plot bar chart
    fig = px.bar(top_scorers_df[::-1],  # reverse so highest is on top in horizontal bar
                 x="Goals", y="Player", orientation='h', 
                 title="Top 10 Goal Scorers", color="Goals", color_continuous_scale="Greens")
    st.plotly_chart(fig, use_container_width=True)

# Section 3: Injuries
elif section == "🤕 Injuries":
    st.subheader("Most Injured Players")
    # Query top injured players (count injuries per player)
    injuries_query = """
        SELECT p.first_name, p.last_name, COUNT(i.injury_id) as injury_count
        FROM Injuries i
        JOIN Players p ON i.player_id = p.player_id
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY injury_count DESC
        LIMIT 10;
    """
    injured_df = pd.read_sql(injuries_query, engine)
    injured_df["Player"] = injured_df["first_name"] + " " + injured_df["last_name"]
    injured_df = injured_df[["Player", "injury_count"]].rename(columns={"injury_count": "Injuries"})
    st.dataframe(injured_df, use_container_width=True)
    # Plot bar chart for injuries
    fig = px.bar(injured_df[::-1], x="Injuries", y="Player", orientation='h',
                 title="Top 10 Most Injury-Prone Players", color="Injuries", color_continuous_scale="OrRd")
    st.plotly_chart(fig, use_container_width=True)

# Section 4: Transfers
elif section == "💰 Transfers":
    st.subheader("Transfer History")
    # Query transfer records
    transfers_query = """
        SELECT p.first_name, p.last_name, c1.club_name AS from_club, c2.club_name AS to_club,
               t.transfer_fee, t.transfer_date
        FROM Transfers t
        JOIN Players p ON t.player_id = p.player_id
        JOIN Clubs c1 ON t.from_club_id = c1.club_id
        JOIN Clubs c2 ON t.to_club_id = c2.club_id
        ORDER BY t.transfer_date DESC;
    """
    transfers_df = pd.read_sql(transfers_query, engine)
    transfers_df["Player"] = transfers_df["first_name"] + " " + transfers_df["last_name"]
    transfers_df.drop(columns=["first_name","last_name"], inplace=True)
    transfers_df.rename(columns={"from_club": "From Club", "to_club": "To Club", 
                                 "transfer_fee": "Fee (€)", "transfer_date": "Date"}, inplace=True)
    st.write(f"**Total Transfers:** {transfers_df.shape[0]}")
    # Display transfers table
    gb = GridOptionsBuilder.from_dataframe(transfers_df)
    gb.configure_pagination(enabled=True, paginationAutoPageSize=True)
    gb.configure_default_column(sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(transfers_df, gridOptions=grid_options, theme='alpine', height=400)
    # Highlight top 5 fees
    top_fees = transfers_df.nlargest(5, "Fee (€)")
    fig = px.bar(top_fees[::-1], x="Fee (€)", y="Player", orientation='h', 
                 title="Top 5 Largest Transfers", color="Fee (€)", color_continuous_scale="Blues")
    st.plotly_chart(fig, use_container_width=True)

# Section 5: Club Analysis
elif section == "🏟️ Club Analysis":
    st.subheader("Club Analysis")
    # Select a club
    clubs_df = pd.read_sql("SELECT club_id, club_name FROM Clubs;", engine)
    club_names = clubs_df["club_name"].sort_values().tolist()
    club_name = st.selectbox("Select Club", club_names)
    club_id = int(clubs_df[clubs_df["club_name"] == club_name]["club_id"].iloc[0])
    # Fetch all matches involving this club
    matches_df = pd.read_sql(f"SELECT * FROM Matches WHERE home_club_id={club_id} OR away_club_id={club_id};", engine)
    if matches_df.empty:
        st.write("No match data available for this club.")
    else:
        played = matches_df.shape[0]
        # Calculate wins, draws, losses
        home_wins = ((matches_df['home_club_id']==club_id) & (matches_df['home_score'] > matches_df['away_score'])).sum()
        away_wins = ((matches_df['away_club_id']==club_id) & (matches_df['away_score'] > matches_df['home_score'])).sum()
        wins = int(home_wins + away_wins)
        draws = ((matches_df['home_score'] == matches_df['away_score'])).sum()
        losses = int(played - wins - draws)
        # Goals for and against
        goals_for = int(matches_df.apply(lambda row: row['home_score'] if row['home_club_id']==club_id else row['away_score'], axis=1).sum())
        goals_against = int(matches_df.apply(lambda row: row['away_score'] if row['home_club_id']==club_id else row['home_score'], axis=1).sum())
        avg_goals = goals_for/played if played else 0.0
        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Matches Played", played)
        col2.metric("Wins", wins)
        col3.metric("Draws", int(draws))
        col1, col2, col3 = st.columns(3)
        col1.metric("Losses", losses)
        col2.metric("Goals Scored", goals_for)
        col3.metric("Goals Conceded", goals_against)
        st.metric("Avg Goals per Match", f"{avg_goals:.2f}")
        # Chart: W/D/L distribution
        outcome_labels = ["Wins", "Draws", "Losses"]
        outcome_counts = [wins, int(draws), losses]
        fig = px.pie(values=outcome_counts, names=outcome_labels, title=f"{club_name} - Win/Draw/Loss")
        st.plotly_chart(fig, use_container_width=True)

# Section 6: Match Stats Overview
elif section == "📊 Match Stats":
    st.subheader("Match Statistics Overview")
    matches_df = pd.read_sql("SELECT * FROM Matches;", engine)
    total_matches = matches_df.shape[0]
    total_goals = int(matches_df["home_score"].sum() + matches_df["away_score"].sum())
    avg_goals = total_goals/total_matches if total_matches else 0.0
    home_wins = ((matches_df['home_score'] > matches_df['away_score']).sum())
    away_wins = ((matches_df['away_score'] > matches_df['home_score']).sum())
    draws = (matches_df['home_score'] == matches_df['away_score']).sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches", total_matches)
    col2.metric("Total Goals", total_goals)
    col3.metric("Avg Goals/Match", f"{avg_goals:.2f}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Home Wins", int(home_wins))
    col2.metric("Away Wins", int(away_wins))
    col3.metric("Draws", int(draws))
    # Bar chart for outcome distribution
    outcomes = {"Home Win": int(home_wins), "Away Win": int(away_wins), "Draw": int(draws)}
    fig = px.bar(x=list(outcomes.keys()), y=list(outcomes.values()),
                 title="Match Outcomes Distribution", labels={"x": "Outcome", "y": "Count"},
                 color=list(outcomes.keys()), color_discrete_sequence=["#6daa2c","#ff4e42","#3366cc"])
    st.plotly_chart(fig, use_container_width=True)
