import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import socket
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="Food Wastage Management System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection configuration


# Load local .env if present
load_dotenv()

# Detect environment: local (default) or cloud
ENV = os.getenv("ENVIRONMENT", "local")

DB_CONFIG = {
    "local": {
        'server': 'INSPIRON-5518\\MSQL',
        'database': 'Foodwastedb',
        'driver': 'ODBC Driver 17 for SQL Server',
        'trusted_connection': 'yes'
    },
    "cloud": {
        'server': "106.215.152.108,1433",   # don’t use os.getenv() directly with values
        'database': "Foodwastedb",
        'driver': 'ODBC Driver 18 for SQL Server',
        'uid': "INSPIRON-5518\Arpit",                 
        'pwd': "Akk_8113",        
        'Encrypt': 'no',
        'TrustServerCertificate': 'yes',
        'Connection Timeout': 30
    }
}

@st.cache_resource
def init_connection(env="local"):
    """Initialize connection to SQL Server"""

    config = DB_CONFIG[env]  # Pick 'local' or 'cloud'

    try:
        if 'uid' in config and 'pwd' in config:
            # SQL Authentication (Cloud)
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['uid']};"
                f"PWD={config['pwd']};"
                f"Encrypt={config.get('Encrypt','no')};"
                f"TrustServerCertificate={config.get('TrustServerCertificate','yes')};"
                f"Connection Timeout={config.get('Connection Timeout',30)};"
            )
        else:
            # Windows Authentication (Local)
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"Trusted_Connection={config['trusted_connection']};"
            )

        conn = pyodbc.connect(conn_str)
        return conn

    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


# 🔹 Auto-detect environment (local vs cloud)
host = socket.gethostname()

if "streamlit" in host.lower():  # Running on Streamlit Cloud
    conn = init_connection(env="cloud")
else:
    conn = init_connection(env="local")


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_data(query):
    """Load data from SQL Server"""
    if conn:
        return pd.read_sql(query, conn)
    return pd.DataFrame()

def execute_query(query, params=None):
    """Execute SQL query with optional parameters"""
    if conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    return False

# Load all tables with correct schema
@st.cache_data
def load_all_data():
    """Load all tables into session state"""
    providers = load_data("SELECT * FROM Providers")
    receivers = load_data("SELECT * FROM Receivers")
    food_listings = load_data("SELECT * FROM Food_Listings_Dataset")
    claims = load_data("SELECT * FROM Claims")
    
    return providers, receivers, food_listings, claims

# Main app
def main():
    st.markdown('<h1 class="main-header">🍽️ Food Wastage Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Food Listings", "Providers", "Receivers", "Claims", "Analytics", "CRUD Operations","EDA Analysis" ,"Queries"]
    )
    
    # Load data
    providers, receivers, food_listings, claims = load_all_data()
    
    if page == "Dashboard":
        show_dashboard(providers, receivers, food_listings, claims)
    elif page == "Food Listings":
        show_food_listings(food_listings, providers)
    elif page == "Providers":
        show_providers(providers)
    elif page == "Receivers":
        show_receivers(receivers)
    elif page == "Claims":
        show_claims(claims, food_listings, receivers)
    elif page == "Analytics":
        show_analytics(providers, receivers, food_listings, claims)
    elif page == "CRUD Operations":
        show_crud_operations()
    elif page == "EDA Analysis":
        show_eda_analysis(providers, receivers, food_listings, claims)
    elif page == "Queries":
        show_queries()

def show_dashboard(providers, receivers, food_listings, claims):
    """Display dashboard with key metrics"""
    st.header("📊 Dashboard Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Providers", len(providers))
    with col2:
        st.metric("Total Receivers", len(receivers))
    with col3:
        st.metric("Total Food Listings", len(food_listings))
    with col4:
        st.metric("Total Claims", len(claims))
    
    # Recent activity
    st.subheader("Recent Activity")
    
    if not food_listings.empty:
        st.dataframe(food_listings.head(10))
    
    # Quick filters
    st.subheader("Quick Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        location_filter = st.selectbox("Filter by Location", ["All"] + food_listings['Location'].unique().tolist() if not food_listings.empty else ["All"])
    
    with col2:
        food_type_filter = st.selectbox("Filter by Food Type", ["All"] + food_listings['Food_Type'].unique().tolist() if not food_listings.empty else ["All"])
    
    if not food_listings.empty:
        filtered_listings = food_listings.copy()
        if location_filter != "All":
            filtered_listings = filtered_listings[filtered_listings['Location'] == location_filter]
        if food_type_filter != "All":
            filtered_listings = filtered_listings[filtered_listings['Food_Type'] == food_type_filter]
        
        st.dataframe(filtered_listings)

def show_food_listings(food_listings, providers):
    """Display food listings with filtering"""
    st.header("🥘 Food Listings")
    
    if food_listings.empty:
        st.warning("No food listings available")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location_filter = st.multiselect("Location", food_listings['Location'].unique())
    with col2:
        food_type_filter = st.multiselect("Food Type", food_listings['Food_Type'].unique())
    with col3:
        provider_type_filter = st.multiselect("Provider Type", food_listings['Provider_Type'].unique())
    
    filtered_listings = food_listings.copy()
    
    if location_filter:
        filtered_listings = filtered_listings[filtered_listings['Location'].isin(location_filter)]
    if food_type_filter:
        filtered_listings = filtered_listings[filtered_listings['Food_Type'].isin(food_type_filter)]
    if provider_type_filter:
        filtered_listings = filtered_listings[filtered_listings['Provider_Type'].isin(provider_type_filter)]
    
    st.dataframe(filtered_listings)
    
    # Add new listing button
    if st.button("Add New Listing"):
        st.session_state.show_add_form = True
    
    if st.session_state.get('show_add_form', False):
        with st.form("add_listing"):
            st.subheader("Add New Food Listing")
            food_name = st.text_input("Food Name")
            quantity = st.number_input("Quantity", min_value=1)
            expiry_date = st.date_input("Expiry Date")
            provider_id = st.number_input("Provider ID", min_value=1)
            provider_type = st.selectbox("Provider Type", ["Supermarket", "Grocery Store", "Restaurant", "Catering Service"])
            location = st.text_input("Location")
            food_type = st.text_input("Food Type")
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            
            submitted = st.form_submit_button("Add Listing")
            if submitted:
                query = """
                INSERT INTO Food_Listings_Dataset (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                if execute_query(query, [food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type]):
                    st.success("Listing added successfully!")
                    st.session_state.show_add_form = False
                    st.rerun()

def show_providers(providers):
    """Display providers information"""
    st.header("🏢 Food Providers")
    
    if providers.empty:
        st.warning("No providers available")
        return
    
    st.dataframe(providers)
    
    # Provider statistics
    st.subheader("Provider Statistics")
    provider_counts = load_data("""
        SELECT p.Name, p.Type, COUNT(f.Food_ID) as TotalListings
        FROM Providers p
        LEFT JOIN Food_Listings_Dataset f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Name, p.Type
        ORDER BY TotalListings DESC
    """)
    st.dataframe(provider_counts)

def show_receivers(receivers):
    """Display receivers information"""
    st.header("👥 Food Receivers")
    
    if receivers.empty:
        st.warning("No receivers available")
        return
    
    st.dataframe(receivers)

def show_claims(claims, food_listings, receivers):
    """Display claims information"""
    st.header("📋 Claims")
    
    if claims.empty or food_listings.empty or receivers.empty:
        st.warning("No claims data available")
        return
    
    try:
        # Check available columns in claims
        claims_cols = claims.columns.tolist()
        receivers_cols = receivers.columns.tolist()
        
        # Build merge step by step
        claims_with_details = claims.copy()
        
        # Merge with food listings
        if 'Food_ID' in claims.columns and 'Food_ID' in food_listings.columns:
            food_cols = ['Food_ID', 'Food_Name', 'Location', 'Food_Type']
            available_food_cols = [col for col in food_cols if col in food_listings.columns]
            if available_food_cols:
                claims_with_details = claims_with_details.merge(
                    food_listings[available_food_cols], 
                    on='Food_ID', how='left'
                )
        
        # Merge with receivers - handle different column names
        receiver_key = None
        if 'Receiver_ID' in claims.columns and 'Receiver_ID' in receivers.columns:
            receiver_key = 'Receiver_ID'
        elif 'ReceiverID' in claims.columns and 'ReceiverID' in receivers.columns:
            receiver_key = 'ReceiverID'
        elif 'ReceiverId' in claims.columns and 'ReceiverId' in receivers.columns:
            receiver_key = 'ReceiverId'
        
        if receiver_key:
            receiver_cols = [receiver_key, 'Name'] if 'Name' in receivers.columns else [receiver_key]
            claims_with_details = claims_with_details.merge(
                receivers[receiver_cols], 
                on=receiver_key, how='left'
            )
        else:
            # Try to find matching columns
            for col in claims.columns:
                if col in receivers.columns and col.endswith('_ID'):
                    claims_with_details = claims_with_details.merge(
                        receivers[['Name']] if 'Name' in receivers.columns else receivers,
                        left_on=col,
                        right_index=False,
                        how='left'
                    )
                    break
        
        st.dataframe(claims_with_details)
        
    except Exception as e:
        st.error(f"Error displaying claims: {str(e)}")
        st.write("Raw claims data:")
        st.dataframe(claims)

def show_analytics(providers, receivers, food_listings, claims):
    """Display analytics and insights"""
    st.header("📈 Analytics & Insights")
    
    if food_listings.empty:
        st.warning("No data available for analytics")
        return
    
    # Food wastage trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Food Type Distribution")
        food_type_counts = food_listings['Food_Type'].value_counts()
        fig = px.pie(values=food_type_counts.values, names=food_type_counts.index)
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("Location-wise Listings")
        location_counts = food_listings['Location'].value_counts()
        fig = px.bar(x=location_counts.index, y=location_counts.values)
        st.plotly_chart(fig)
    
    # Top providers
    st.subheader("Top Food Providers")
    top_providers = load_data("""
        SELECT TOP 10 
            p.Name as ProviderName,
            p.Type as ProviderType,
            COUNT(f.Food_ID) as TotalListings,
            SUM(f.Quantity) as TotalQuantity
        FROM Providers p
        JOIN Food_Listings_Dataset f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Name, p.Type
        ORDER BY TotalListings DESC
    """)
    st.dataframe(top_providers)
    
    # High demand locations
    st.subheader("High Demand Locations")
    demand_locations = load_data("""
        SELECT 
            f.Location,
            COUNT(c.Claim_ID) as TotalClaims,
            SUM(f.Quantity) as TotalQuantityClaimed
        FROM Food_Listings_Dataset f
        JOIN Claims c ON f.Food_ID = c.Food_ID
        GROUP BY f.Location
        ORDER BY TotalClaims DESC
    """)
    st.dataframe(demand_locations)

def show_crud_operations():
    """Display CRUD operations interface"""
    st.header("🔧 CRUD Operations")
    
    operation = st.selectbox("Select Operation", ["Create", "Read", "Update", "Delete"])
    table = st.selectbox("Select Table", ["Providers", "Receivers", "Food_Listings_Dataset", "Claims"])
    
    if operation == "Create":
        show_create_form(table)
    elif operation == "Read":
        show_read_table(table)
    elif operation == "Update":
        show_update_form(table)
    elif operation == "Delete":
        show_delete_form(table)

def show_create_form(table):
    """Show create form for selected table"""
    st.subheader(f"Add New {table}")
    
    if table == "Providers":
        with st.form("add_provider"):
            name = st.text_input("Name")
            type_ = st.selectbox("Type", ["Supermarket", "Grocery Store", "Restaurant", "Catering Service"])
            address = st.text_input("Address")
            city = st.text_input("City")
            contact = st.text_input("Contact")
            
            submitted = st.form_submit_button("Add Provider")
            if submitted:
                query = "INSERT INTO Providers (Name, Type, Address, City, Contact) VALUES (?, ?, ?, ?, ?)"
                if execute_query(query, [name, type_, address, city, contact]):
                    st.success("Provider added successfully!")
                    st.rerun()
    
    elif table == "Receivers":
        with st.form("add_receiver"):
            name = st.text_input("Name")
            type_ = st.selectbox("Type", ["Charity", "Food Bank", "Shelter", "Community Center"])
            city = st.text_input("City")
            contact = st.text_input("Contact")
            
            submitted = st.form_submit_button("Add Receiver")
            if submitted:
                query = "INSERT INTO Receivers (Name, Type, City, Contact) VALUES (?, ?, ?, ?)"
                if execute_query(query, [name, type_, city, contact]):
                    st.success("Receiver added successfully!")
                    st.rerun()

def show_read_table(table):
    """Display table data"""
    st.subheader(f"{table} Data")
    data = load_data(f"SELECT * FROM {table}")
    st.dataframe(data)

def show_update_form(table):
    """Show update form for selected table"""
    st.subheader(f"Update {table}")
    
    data = load_data(f"SELECT * FROM {table}")
    if data.empty:
        st.warning("No data available")
        return
    
    if not data.empty:
        id_col = f"{'Provider_ID' if table == 'Providers' else 'Receiver_ID' if table == 'Receivers' else 'Food_ID' if table == 'Food_Listings_Dataset' else 'Claim_ID'}"
        selected_id = st.selectbox(f"Select ID to update", data[id_col].tolist())
        
        selected_row = data[data[id_col] == selected_id].iloc[0]
        
        with st.form("update_form"):
            if table == "Providers":
                name = st.text_input("Name", value=selected_row['Name'])
                type_ = st.selectbox("Type", ["Supermarket", "Grocery Store", "Restaurant", "Catering Service"], 
                                   index=["Supermarket", "Grocery Store", "Restaurant", "Catering Service"].index(selected_row['Type']))
                address = st.text_input("Address", value=selected_row['Address'])
                city = st.text_input("City", value=selected_row['City'])
                contact = st.text_input("Contact", value=selected_row['Contact'])
                
                if st.form_submit_button("Update Provider"):
                    query = "UPDATE Providers SET Name=?, Type=?, Address=?, City=?, Contact=? WHERE Provider_ID=?"
                    if execute_query(query, [name, type_, address, city, contact, selected_id]):
                        st.success("Provider updated successfully!")
                        st.rerun()

def show_delete_form(table):
    """Show delete form for selected table"""
    st.subheader(f"Delete from {table}")
    
    data = load_data(f"SELECT * FROM {table}")
    if data.empty:
        st.warning("No data available")
        return
    
    if not data.empty:
        id_col = f"{'Provider_ID' if table == 'Providers' else 'Receiver_ID' if table == 'Receivers' else 'Food_ID' if table == 'Food_Listings_Dataset' else 'Claim_ID'}"
        selected_id = st.selectbox(f"Select ID to delete", data[id_col].tolist())
        
        if st.button("Delete"):
            query = f"DELETE FROM {table} WHERE {id_col}=?"
            if execute_query(query, [selected_id]):
                st.success(f"Record deleted successfully!")
                st.rerun()

def show_queries():
    """Display all 13 queries with results"""
    st.header("📊 All 13 Queries with Results")
    
    queries = {
        "Query 1: How many food providers and receivers are there in each city?": """
            SELECT 
                City,
                COUNT(DISTINCT Provider_ID) AS Total_Providers,
                COUNT(DISTINCT Receiver_ID) AS Total_Receivers
            FROM (
                SELECT City, Provider_ID, NULL AS Receiver_ID FROM Providers
                UNION ALL
                SELECT City, NULL AS Provider_ID, Receiver_ID FROM Receivers
            ) AS combined
            GROUP BY City
            ORDER BY City;
        """,
        
        "Query 2: Which type of food provider (restaurant, grocery store, etc.) contributes the most food?": """
            SELECT TOP 1 
                p.Type AS Provider_Type,
                SUM(f.Quantity) AS Total_Quantity
            FROM Providers p
            JOIN Food_Listings_Dataset f
                ON p.Provider_ID = f.Provider_ID
            GROUP BY p.Type
            ORDER BY Total_Quantity DESC;
        """,
        
        "Query 3: What is the contact information of food providers in a specific city?": """
            DECLARE @city_name VARCHAR(100) = 'Adambury';
            SELECT 
                Name,
                Type,
                Address,
                City,
                Contact
            FROM Providers
            WHERE City = @city_name
            ORDER BY Name
            OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;
        """,
        
        "Query 4: Which receivers have claimed the most food?": """
            SELECT 
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM Claims c
            JOIN Receivers r 
                ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY Total_Claims DESC;
        """,
        
        "Query 5: Total quantity of food available from all providers": """
            SELECT SUM(Quantity) AS Total_Quantity_Available
            FROM Food_Listings_Dataset;
        """,
        
        "Query 6: Which city has the highest number of food listings": """
            SELECT TOP 1 WITH TIES
                p.City,
                COUNT(f.Food_ID) AS Total_Listings
            FROM Food_Listings_Dataset f
            JOIN Providers p
                ON f.Provider_ID = p.Provider_ID
            GROUP BY p.City
            ORDER BY Total_Listings DESC;
        """,
        
        "Query 7: Most commonly available food types": """
            SELECT 
                Food_Type,
                COUNT(Food_ID) AS Listings_Count
            FROM Food_Listings_Dataset
            GROUP BY Food_Type
            ORDER BY Listings_Count DESC;
        """,
        
        "Query 8: How many food claims have been made for each food item?": """
            SELECT 
                fl.Food_Name,
                COUNT(c.Claim_ID) AS TotalClaims
            FROM Food_Listings_Dataset fl
            LEFT JOIN Claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Food_Name
            ORDER BY TotalClaims DESC;
        """,
        
        "Query 9: Which provider has had the highest number of successful food claims?": """
            SELECT TOP 1
                p.Name AS ProviderName,
                COUNT(c.Claim_ID) AS SuccessfulClaims
            FROM Providers p
            JOIN Food_Listings_Dataset fl ON p.Provider_ID = fl.Provider_ID
            JOIN Claims c ON fl.Food_ID = c.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Name
            ORDER BY SuccessfulClaims DESC;
        """,
        
        "Query 10: What percentage of food claims are completed vs. pending vs. canceled?": """
            SELECT 
                Status,
                COUNT(*) AS Count,
                ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Claims)), 2) AS Percentage
            FROM Claims
            GROUP BY Status;
        """,
        
        "Query 11: Average quantity of food claimed per receiver": """
            SELECT 
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                AVG(f.Quantity) AS Avg_Quantity_Claimed
            FROM Claims c
            JOIN Food_Listings_Dataset f
                ON c.Food_ID = f.Food_ID
            JOIN Receivers r
                ON c.Receiver_ID = r.Receiver_ID
            WHERE c.Status = 'Completed'
            GROUP BY r.Receiver_ID, r.Name;
        """,
        
        "Query 12: Meal type claimed the most": """
            SELECT TOP 1
                f.Meal_Type,
                COUNT(*) AS Claim_Count
            FROM Claims c
            JOIN Food_Listings_Dataset f
                ON c.Food_ID = f.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY f.Meal_Type
            ORDER BY Claim_Count DESC;
        """,
        
        "Query 13: Total quantity of food donated by each provider": """
            SELECT 
                p.Provider_ID,
                p.Name AS Provider_Name,
                SUM(f.Quantity) AS Total_Quantity_Donated
            FROM Food_Listings_Dataset f
            JOIN Providers p
                ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY Total_Quantity_Donated DESC;
        """
    }
    
    for query_name, query in queries.items():
        with st.expander(query_name):
            st.code(query, language="sql")
            result = load_data(query)
            if not result.empty:
                st.dataframe(result)
                
                # Visualize if appropriate
                if len(result.columns) >= 2 and len(result) > 1:
                    if 'Total' in str(result.columns[-1]) or 'Count' in str(result.columns[-1]):
                        fig = px.bar(result, x=result.columns[0], y=result.columns[-1])
                        st.plotly_chart(fig)

def show_eda_analysis(providers, receivers, food_listings, claims):
    """Display comprehensive EDA analysis from food.ipynb"""
    st.header("📊 EDA Analysis - Food Waste Management Insights")
    
    # Create tabs for each EDA query
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
        "City Distribution", "Top Provider Types", "Contact Info", "Top Receivers",
        "Total Food Available", "Top Cities", "Food Types", "Food Claims",
        "Successful Providers", "Claim Status", "Avg Claims", "Meal Types", "Donations"
    ])
    
    with tab1:
        st.subheader("Query 1: Food Providers and Receivers by City")
        query1 = """
            SELECT 
                City,
                COUNT(DISTINCT Provider_ID) AS Total_Providers,
                COUNT(DISTINCT Receiver_ID) AS Total_Receivers
            FROM (
                SELECT City, Provider_ID, NULL AS Receiver_ID FROM Providers
                UNION ALL
                SELECT City, NULL AS Provider_ID, Receiver_ID FROM Receivers
            ) AS combined
            GROUP BY City
            ORDER BY City;
        """
        result1 = load_data(query1)
        if not result1.empty:
            st.dataframe(result1)
            fig = px.bar(result1, x='City', y=['Total_Providers', 'Total_Receivers'], 
                        title="Providers vs Receivers by City")
            st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Query 2: Top Food Provider Types by Contribution")
        query2 = """
            SELECT TOP 5
                p.Type AS Provider_Type,
                SUM(f.Quantity) AS Total_Quantity
            FROM Providers p
            JOIN Food_Listings_Dataset f
                ON p.Provider_ID = f.Provider_ID
            GROUP BY p.Type
            ORDER BY Total_Quantity DESC;
        """
        result2 = load_data(query2)
        if not result2.empty:
            st.dataframe(result2)
            fig = px.pie(result2, values='Total_Quantity', names='Provider_Type',
                        title="Food Contribution by Provider Type")
            st.plotly_chart(fig)
    
    with tab3:
        st.subheader("Query 3: Contact Information of Food Providers")
        city_name = st.text_input("Enter city name:", "Adambury")
        query3 = f"""
            SELECT 
                Name,
                Type,
                Address,
                City,
                Contact
            FROM Providers
            WHERE City = '{city_name}'
            ORDER BY Name;
        """
        result3 = load_data(query3)
        if not result3.empty:
            st.dataframe(result3)
            st.download_button(
                label="Download Contact Info",
                data=result3.to_csv(index=False),
                file_name=f"providers_{city_name}.csv",
                mime="text/csv"
            )
    
    with tab4:
        st.subheader("Query 4: Top Receivers by Claims")
        query4 = """
            SELECT TOP 10
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM Claims c
            JOIN Receivers r 
                ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY Total_Claims DESC;
        """
        result4 = load_data(query4)
        if not result4.empty:
            st.dataframe(result4)
            fig = px.bar(result4, x='Receiver_Name', y='Total_Claims',
                        title="Top Receivers by Number of Claims")
            st.plotly_chart(fig)
    
    with tab5:
        st.subheader("Query 5: Total Quantity of Food Available")
        query5 = """
            SELECT SUM(Quantity) AS Total_Quantity_Available
            FROM Food_Listings_Dataset;
        """
        result5 = load_data(query5)
        if not result5.empty:
            total_quantity = result5.iloc[0]['Total_Quantity_Available']
            st.metric("Total Food Available", f"{total_quantity:,} units")
            st.dataframe(result5)
    
    with tab6:
        st.subheader("Query 6: Cities with Highest Food Listings")
        query6 = """
            SELECT TOP 10
                p.City,
                COUNT(f.Food_ID) AS Total_Listings
            FROM Food_Listings_Dataset f
            JOIN Providers p
                ON f.Provider_ID = p.Provider_ID
            GROUP BY p.City
            ORDER BY Total_Listings DESC;
        """
        result6 = load_data(query6)
        if not result6.empty:
            st.dataframe(result6)
            fig = px.bar(result6, x='City', y='Total_Listings',
                        title="Top Cities by Food Listings")
            st.plotly_chart(fig)
    
    with tab7:
        st.subheader("Query 7: Most Common Food Types")
        query7 = """
            SELECT TOP 10
                Food_Type,
                COUNT(Food_ID) AS Listings_Count
            FROM Food_Listings_Dataset
            GROUP BY Food_Type
            ORDER BY Listings_Count DESC;
        """
        result7 = load_data(query7)
        if not result7.empty:
            st.dataframe(result7)
            fig = px.pie(result7, values='Listings_Count', names='Food_Type',
                        title="Distribution of Food Types")
            st.plotly_chart(fig)
    
    with tab8:
        st.subheader("Query 8: Food Claims by Food Item")
        query8 = """
            SELECT TOP 15
                fl.Food_Name,
                COUNT(c.Claim_ID) AS TotalClaims
            FROM Food_Listings_Dataset fl
            LEFT JOIN Claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Food_Name
            ORDER BY TotalClaims DESC;
        """
        result8 = load_data(query8)
        if not result8.empty:
            st.dataframe(result8)
            fig = px.bar(result8, x='Food_Name', y='TotalClaims',
                        title="Most Claimed Food Items")
            st.plotly_chart(fig)
    
    with tab9:
        st.subheader("Query 9: Top Providers by Successful Claims")
        query9 = """
            SELECT TOP 10
                p.Name AS ProviderName,
                COUNT(c.Claim_ID) AS SuccessfulClaims
            FROM Providers p
            JOIN Food_Listings_Dataset fl ON p.Provider_ID = fl.Provider_ID
            JOIN Claims c ON fl.Food_ID = c.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Name
            ORDER BY SuccessfulClaims DESC;
        """
        result9 = load_data(query9)
        if not result9.empty:
            st.dataframe(result9)
            fig = px.bar(result9, x='ProviderName', y='SuccessfulClaims',
                        title="Top Providers by Successful Claims")
            st.plotly_chart(fig)
    
    with tab10:
        st.subheader("Query 10: Claim Status Distribution")
        query10 = """
            SELECT 
                Status,
                COUNT(*) AS Count,
                ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Claims)), 2) AS Percentage
            FROM Claims
            GROUP BY Status;
        """
        result10 = load_data(query10)
        if not result10.empty:
            st.dataframe(result10)
            fig = px.pie(result10, values='Percentage', names='Status',
                        title="Claim Status Distribution")
            st.plotly_chart(fig)
    
    with tab11:
        st.subheader("Query 11: Average Quantity Claimed per Receiver")
        query11 = """
            SELECT TOP 15
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                AVG(f.Quantity) AS Avg_Quantity_Claimed
            FROM Claims c
            JOIN Food_Listings_Dataset f
                ON c.Food_ID = f.Food_ID
            JOIN Receivers r
                ON c.Receiver_ID = r.Receiver_ID
            WHERE c.Status = 'Completed'
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY Avg_Quantity_Claimed DESC;
        """
        result11 = load_data(query11)
        if not result11.empty:
            st.dataframe(result11)
            fig = px.bar(result11, x='Receiver_Name', y='Avg_Quantity_Claimed',
                        title="Average Quantity Claimed per Receiver")
            st.plotly_chart(fig)
    
    with tab12:
        st.subheader("Query 12: Most Claimed Meal Types")
        query12 = """
            SELECT 
                f.Meal_Type,
                COUNT(*) AS Claim_Count
            FROM Claims c
            JOIN Food_Listings_Dataset f
                ON c.Food_ID = f.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY f.Meal_Type
            ORDER BY Claim_Count DESC;
        """
        result12 = load_data(query12)
        if not result12.empty:
            st.dataframe(result12)
            fig = px.pie(result12, values='Claim_Count', names='Meal_Type',
                        title="Most Claimed Meal Types")
            st.plotly_chart(fig)
    
    with tab13:
        st.subheader("Query 13: Total Quantity Donated by Each Provider")
        query13 = """
            SELECT TOP 15
                p.Provider_ID,
                p.Name AS Provider_Name,
                SUM(f.Quantity) AS Total_Quantity_Donated
            FROM Food_Listings_Dataset f
            JOIN Providers p
                ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY Total_Quantity_Donated DESC;
        """
        result13 = load_data(query13)
        if not result13.empty:
            st.dataframe(result13)
            fig = px.bar(result13, x='Provider_Name', y='Total_Quantity_Donated',
                        title="Total Quantity Donated by Providers")
            st.plotly_chart(fig)

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False


if __name__ == "__main__":
    main()
