import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import *
from plotly.graph_objs.scatter.marker import Line
from plotly.subplots import make_subplots
import numpy as np
import plot_settings
from multiapp import MultiApp
import plot_functions

# load soco data
@st.cache
def load_and_format_data(d):
    d.columns = [x.lower().replace(' ','_') for x in d.columns]

    d.select_dtypes(include=['object']).apply(lambda x: x.str.replace('*', '', regex=True).str.title())
