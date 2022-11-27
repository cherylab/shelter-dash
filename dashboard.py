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
import data_functions
import calendar

st.set_page_config(layout="wide")

# -----------------------------------------------
# Load the in/out data
iodf = data_functions.data_ins_outs()

# -----------------------------------------------
# Common dictionaries/variables
INTAKE_MAPPING = {'intake_domestic_agency':'Other Agency',
                  'intake_impound_seizure':'Impound/Seizure',
                  'intake_intl_agency':'Other Agency',
                  'intake_oie':'Owner Intended Euth.',
                  'intake_other':'Other',
                  'intake_owner_giveup':'Owner Give-Up',
                  'intake_state_agency':'Other Agency',
                  'intake_stray':'Stray'}

OUTCOME_MAPPING = {'out_adopt':'Adopted',
                   'out_return_owner':'Return to Owner',
                   'out_state_agency':'Other Agency',
                   'out_domestic_agency':'Other Agency',
                   'out_intl_agency':'Other Agency',
                   'out_return_field':'Return to Field',
                   'out_other':'Other',
                   'died_in_care':'Died in Care',
                   'lost_in_care':'Lost in Care',
                   'euthanasia':'Euthanized',
                   'oie':'Euthanized'}

AGE_GROUPS = ['0-1 Wk','2-7 Wks','2-5 Mos','6-11 Mos','1 Yr','2 Yrs','3 Yrs','4 Yrs','5 Yrs','6 Yrs','7 Yrs',
              '8 Yrs','9 Yrs','10 Yrs','11 Yrs','12 Yrs','13 Yrs','14 Yrs','15 Yrs','16 Yrs','17 Yrs','18 Yrs',
              '19 Yrs','20 Yrs']

# -----------------------------------------------
# Sidebar inputs

# -----------------------------------------------
# 1st: General summary page
def general_page(iodf):
    st.title('General Summary')

    # -----------------------------------------------
    # SIDEBAR INPUTS
    st.sidebar.write("<br>", unsafe_allow_html=True)
    with st.sidebar.form(key='date_form_general'):
        st.write('<b>Date Inputs</b>', unsafe_allow_html=True)
        start_date = st.date_input('Choose a start date',
                                          value=iodf.intake_date.min(),
                                          min_value=iodf.intake_date.min(),
                                          max_value=datetime.datetime.today(),
                                          key='start_general')
        end_date = st.date_input('Choose an end date',
                                        value=iodf.intake_date.max(),
                                        min_value=iodf.intake_date.min(),
                                        max_value=datetime.datetime.today(),
                                        key='end_general')

        # convert chosen dates to be datetime.datetime instead of datetime.date
        start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)
        end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)

        # create the first of the month versions of the chosen dates
        start_month = datetime.datetime(start_date.year, start_date.month, 1)
        end_month = datetime.datetime(end_date.year, end_date.month, 1)

        st.write(f'NOTE: Monthly analyses will cover all data for <b>{start_date.strftime("%b-%-Y")}</b> '
                 f'through <b>{end_date.strftime("%b-%-Y")}</b>, even if those months do not have data for the full '
                 f'month.', unsafe_allow_html=True)

        submit_button_first = st.form_submit_button('Submit', help='Press to recalculate')

    # add some columns to the in/out df
    iodf = data_functions.add_columns_ins_outs(iodf)

    # expand dataframe to have 1 row per month for every month each pet is in the shelter, and then filter to just the
    # months that are chosen in the inputs
    bymonth = data_functions.date_filter_month_firsts(iodf, start_month, end_month)
    # -----------------------------------------------

    # TOTAL ANIMALS EXPANDER
    total_animals_expander = st.beta_expander('How many animals are in the shelter?', expanded=True)
    with total_animals_expander:
        # do data manipulations for waterfall plot
        monthtot, bymonth, bymonth_types = data_functions.monthly_in_out_data_prep(bymonth)

        # create waterfall plot
        plot_functions.monthly_in_out_waterfall_plot(monthtot)

        # create in/out bar plot
        plot_functions.monthly_in_out_bar_plot(bymonth_types)

    # create a df with just the animals from the last month chosen - to be used in all below analysis on this page
    lastmonth = bymonth[bymonth.months == end_month]

    # filter the main iodf to just the months chosen in the inputs - do this by using the already date filtered bymonth
    # dataframe, and then selecting only the pets in bymonth from iodf using their id number... that way, iodf will now
    # be 1 row per pet only for those pets in the shelter during the chosen timeframe
    iodf = iodf[iodf['id'].isin(bymonth['id'])]

    # AGE EXPANDER
    age_expander = st.beta_expander('How old are animals in the shelter?', expanded=False)
    with age_expander:
        lastmonth, lastmo_age = data_functions.age_breakdown_asof_today_data_prep(lastmonth, end_date)
        iodf, hist_age = data_functions.age_breakdown_asof_today_data_prep(iodf, end_date)

        age_lastmo = plot_functions.age_breakdown_bar_plot(lastmo_age, period='lastmonth')
        st.plotly_chart(age_lastmo, use_container_width=True)

        age_hist = plot_functions.age_breakdown_bar_plot(hist_age, period='history')
        st.plotly_chart(age_hist, use_container_width=True)

    # LENGTH OF STAY EXPANDER
    length_stay_expander = st.beta_expander('How long do animals stay in the shelter?', expanded=False)
    with length_stay_expander:
        lastmonth = data_functions.length_stay_violin_data_prep(lastmonth)
        iodf = data_functions.length_stay_violin_data_prep(iodf)

        length_lastmo = plot_functions.length_stay_violin_plot(lastmonth, period='lastmonth')
        st.plotly_chart(length_lastmo, use_container_width=True)

        length_hist = plot_functions.length_stay_violin_plot(iodf, period='history')
        st.plotly_chart(length_hist, use_container_width=True)

    # BREED EXPANDER
    breed_expander = st.beta_expander('What breeds of animals are in the shelter?', expanded=False)
    with breed_expander:
        lastmo_breed = data_functions.breed_breakdown_data_prep(lastmonth)
        hist_breed = data_functions.breed_breakdown_data_prep(iodf)

        breed1, breed2 = st.beta_columns((.5, .5))
        breed_lastmo = plot_functions.breed_breakdown_bar_plot(lastmo_breed, period='lastmonth')
        breed1.plotly_chart(breed_lastmo, use_container_width=True)

        breed_hist = plot_functions.breed_breakdown_bar_plot(hist_breed, period='history')
        breed2.plotly_chart(breed_hist, use_container_width=True)

# -----------------------------------------------
# 2nd page: intakes page
def intake_page(iodf, INTAKE_MAPPING):
    st.title('Intakes')

    # -----------------------------------------------
    # SIDEBAR INPUTS
    st.sidebar.write("<br>", unsafe_allow_html=True)
    with st.sidebar.form(key='date_form_ins'):
        st.write('<b>Date Inputs</b>', unsafe_allow_html=True)
        start_date = st.date_input('Choose a start date',
                                          value=iodf.intake_date.min(),
                                          min_value=iodf.intake_date.min(),
                                          max_value=datetime.datetime.today(),
                                          key='start_ins')
        end_date = st.date_input('Choose an end date',
                                        value=iodf.intake_date.max(),
                                        min_value=iodf.intake_date.min(),
                                        max_value=datetime.datetime.today(),
                                        key='end_ins')

        # convert chosen dates to be datetime.datetime instead of datetime.date
        start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)
        end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)

        # create the first of the month versions of the chosen dates
        start_month = datetime.datetime(start_date.year, start_date.month, 1)
        end_month = datetime.datetime(end_date.year, end_date.month, 1)

        # create the note to go with the date filter
        start_day = start_date.day == 1
        end_day = end_date.day == calendar.monthrange(end_date.year, end_date.month)[1]

        note = ""
        if (start_day==False) | (end_day==False):
            note += "NOTE: "
        if start_day==False:
            note += f"<b>{start_date.strftime('%b-%-Y')}</b> data excludes the first <b>{start_date.day - 1}</b> day(s). "
        if end_day == False:
            if end_date.day != 1:
                note += f"<b>{end_date.strftime('%b-%-Y')}</b> data only includes days <b>1-{end_date.day}</b>."
            else:
                note += f"<b>{end_date.strftime('%b-%-Y')}</b> data only includes the <b>1st</b>."

        if note != "":
            st.write(note, unsafe_allow_html=True)

        submit_button_first = st.form_submit_button('Submit', help='Press to recalculate')

    # add some columns to the in/out df & calculate age at intake
    iodf = data_functions.add_columns_ins_outs(iodf)
    iodf = data_functions.age_calc_at_in_out(iodf, date_for_comp='intake')
    iodf = iodf[(iodf.intake_date >= start_date) & (iodf.intake_date <= end_date)]
    # -----------------------------------------------

    # MONTHLY TOTALS EXPANDER
    totals_expander = st.beta_expander('Intake total calendar trends', expanded=True)
    with totals_expander:
        ins_month = data_functions.inout_heatmap_data_prep(iodf, date_for_comp='intake')
        plot_functions.inout_monthly_heatmap_plot(ins_month, date_for_comp='intake')

    # INTAKE TYPES EXPANDER
    types_expander = st.beta_expander('Intake types', expanded=False)
    with types_expander:
        intype_month, intype_qtr = data_functions.inout_types_month_data_prep(iodf, INTAKE_MAPPING,
                                                                              date_for_comp='intake')

        plot_functions.inout_types_stacked_bar_plot(intype_month, date_for_comp='intake')
        type1, space, type2 = st.beta_columns((.25,.02,1))
        # with type1:
        chosen_comps = type1.multiselect(label='Choose up to 3 input types for monthly comparison',
                       options=sorted(intype_month.type.unique().tolist()),
                       default=['Other Agency','Stray'])
        # with type2:
        comparison_plot = plot_functions.inout_types_bar_comparison_plot(intype_month, chosen_comps,
                                                                         date_for_comp='intake')
        type2.plotly_chart(comparison_plot, use_container_width=True)

        plot_functions.inout_types_quarter_line_plot(intype_qtr, date_for_comp='intake')

    # AGENCY EXPANDER
    agency_expander = st.beta_expander('Intake agencies', expanded=False)
    with agency_expander:
        agencydf = data_functions.inout_agencies_data_prep(iodf, date_for_comp='intake')
        plot_functions.inout_agency_bar_plot(agencydf, date_for_comp='intake')

    # BREED EXPANDER
    breed_expander = st.beta_expander('Intake breeds', expanded=False)
    with breed_expander:
        breeddf = data_functions.inout_breed_data_prep(iodf, start_month, end_month, date_for_comp='intake')

        breed1, sp, breed2 = st.beta_columns((.25,.02,1))
        species = breed1.selectbox(label='Choose an animal type',
                                   options=sorted(breeddf.type.unique().tolist()),
                                   index=0,
                                   key='breeds')

        breed1.write("<br>", unsafe_allow_html=True)

        max_base = breed1.radio(label='Popular breeds based on:',
                                options=['Full History','Latest Month'],
                                index=0,
                                key='breeds')
        max_base_dict = {'Full History':'history', 'Latest Month':'latest'}

        breed1.write("<br>", unsafe_allow_html=True)

        perc = breed1.checkbox(label='Show values as % of total animals',
                               value=False,
                               key='breeds')

        breed_fig = plot_functions.inout_breed_line_plot(breeddf, species, perc=perc, max_base=max_base_dict[max_base],
                                                         date_for_comp='intake')

        breed2.plotly_chart(breed_fig, use_container_width=True)

    # AGE EXPANDER
    age_expander = st.beta_expander('Intake ages', expanded=False)
    with age_expander:
        agedf = data_functions.inout_age_data_prep(iodf, start_month, end_month, AGE_GROUPS, date_for_comp='intake')

        age1, sp, age2 = st.beta_columns((.25, .02, 1))
        species_age = age1.selectbox(label='Choose an animal type',
                                 options=sorted(breeddf.type.unique().tolist()),
                                 index=0,
                                 key='age')

        age1.write("<br>", unsafe_allow_html=True)

        max_base_age = age1.radio(label='Popular ages based on:',
                              options=['Full History', 'Latest Month'],
                              index=0,
                              key='age')

        age1.write("<br>", unsafe_allow_html=True)

        perc_age = age1.checkbox(label='Show values as % of total animals',
                             value=False,
                             key='age')

        age_fig = plot_functions.inout_age_line_plot(agedf, species_age, AGE_GROUPS, perc=perc_age,
                                                      max_base=max_base_dict[max_base_age], date_for_comp='intake')

        age2.plotly_chart(age_fig, use_container_width=True)

# -----------------------------------------------
# 3rd: Outcomes page
def outcome_page(iodf):
    st.title('Outcomes')

    # -----------------------------------------------
    # SIDEBAR INPUTS
    st.sidebar.write("<br>", unsafe_allow_html=True)
    with st.sidebar.form(key='date_form_outs'):
        st.write('<b>Date Inputs</b>', unsafe_allow_html=True)
        start_date = st.date_input('Choose a start date',
                                   value=iodf.out_date.min(),
                                   min_value=iodf.out_date.min(),
                                   max_value=datetime.datetime.today(),
                                   key='start_outs')
        end_date = st.date_input('Choose an end date',
                                 value=iodf.out_date.max(),
                                 min_value=iodf.out_date.min(),
                                 max_value=datetime.datetime.today(),
                                 key='end_outs')

        # convert chosen dates to be datetime.datetime instead of datetime.date
        start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)
        end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)

        # create the first of the month versions of the chosen dates
        start_month = datetime.datetime(start_date.year, start_date.month, 1)
        end_month = datetime.datetime(end_date.year, end_date.month, 1)

        # create the note to go with the date filter
        start_day = start_date.day == 1
        end_day = end_date.day == calendar.monthrange(end_date.year, end_date.month)[1]

        note = ""
        if (start_day == False) | (end_day == False):
            note += "NOTE: "
        if start_day == False:
            note += f"<b>{start_date.strftime('%b-%-Y')}</b> data excludes the first <b>{start_date.day - 1}</b> day(s). "
        if end_day == False:
            if end_date.day != 1:
                note += f"<b>{end_date.strftime('%b-%-Y')}</b> data only includes days <b>1-{end_date.day}</b>."
            else:
                note += f"<b>{end_date.strftime('%b-%-Y')}</b> data only includes the <b>1st</b>."

        if note != "":
            st.write(note, unsafe_allow_html=True)

        submit_button_first = st.form_submit_button('Submit', help='Press to recalculate')

    # add some columns to the in/out df & calculate age at intake
    iodf = data_functions.add_columns_ins_outs(iodf)

    # number used for save rates calc
    total_animals = iodf.id.nunique()
    total_outcome_animals = iodf[iodf.out_date.notnull()].id.nunique()
    total_adopted_animals = iodf[iodf.out_adopt==1].id.nunique()

    # filter to just animals with an out date in the chosen timeframe, and then calculate age at out date
    iodf = iodf[(iodf.out_date >= start_date) & (iodf.out_date <= end_date)]
    iodf = data_functions.age_calc_at_in_out(iodf, date_for_comp='out')
    iodf = data_functions.length_stay_calc(iodf)
    # -----------------------------------------------

    # st.write(iodf)

    # SAVE RATES
    saverate_expander = st.beta_expander('Save rates', expanded=True)
    with saverate_expander:
        outcome_animals = iodf.id.nunique()
        adopted_animals = iodf[iodf.out_adopt==1].id.nunique()

        save1, sp, save2 = st.beta_columns((1,.02,1))
        st.markdown(""" <style> .labels {
            font-size:20px ; font-family: 'Avenir'; color: #4c4c4c;} 
            </style> """, unsafe_allow_html=True)
        st.markdown(""" <style> .values {
            font-size:30px ; font-family: 'Avenir'; color: #1f78b4;} 
            </style> """, unsafe_allow_html=True)
        st.markdown(""" <style> .note {
                font-size:10px ; font-family: 'Avenir'; color: #4c4c4c;} 
                </style> """, unsafe_allow_html=True)
        save1.write('<br>', unsafe_allow_html=True)
        save1.markdown('<p class="labels">Full history save rate</p>', unsafe_allow_html=True)
        save1.markdown(f'<p class="values">{total_adopted_animals / total_outcome_animals:.0%}</p>', unsafe_allow_html=True)
        # save1.write('<p class="note">(based on total animals that have ever left the shelter</p>', unsafe_allow_html=True)
        # save1.markdown(f'<p class="values">{total_adopted_animals/total_animals:.0%}</p>', unsafe_allow_html=True)
        # save1.write('<p class="note">(based on total animals that have ever passed through the shelter, '
        #             'including those who are still there</p>', unsafe_allow_html=True)

        save2.markdown('<p class="labels">Time period save rate</p>', unsafe_allow_html=True)
        save2.markdown(f'<p class="values">{adopted_animals / outcome_animals:.0%}</p>', unsafe_allow_html=True)
        save2.write('<p class="note">(based on total animals that left the shelter during the chosen time frame</p>',
                    unsafe_allow_html=True)

    # MONTHLY TOTALS EXPANDER
    totals_expander = st.beta_expander('Outcome total calendar trends', expanded=False)
    with totals_expander:
        outs_month = data_functions.inout_heatmap_data_prep(iodf, date_for_comp='out')
        plot_functions.inout_monthly_heatmap_plot(outs_month, date_for_comp='out')

    # OUTCOME LENGTH OF STAY EXPANDER
    lengthstay_expander = st.beta_expander('Outcome length of stays', expanded=False)

    # INTAKE TYPES EXPANDER
    types_expander = st.beta_expander('Outcome types', expanded=False)
    with types_expander:
        outtype_month, outtype_qtr = data_functions.inout_types_month_data_prep(iodf, OUTCOME_MAPPING,
                                                                                date_for_comp='out')

        plot_functions.inout_types_stacked_bar_plot(outtype_month, date_for_comp='out')
        type1, space, type2 = st.beta_columns((.25,.02,1))
        # with type1:
        chosen_comps = type1.multiselect(label='Choose up to 3 outcome types for monthly comparison',
                       options=sorted(outtype_month.type.unique().tolist()),
                       default=['Adopted','Other Agency'])
        # with type2:
        comparison_plot = plot_functions.inout_types_bar_comparison_plot(outtype_month, chosen_comps,
                                                                         date_for_comp='out')
        type2.plotly_chart(comparison_plot, use_container_width=True)

        plot_functions.inout_types_quarter_line_plot(outtype_qtr, date_for_comp='out')

    # AGENCY EXPANDER
    agency_expander = st.beta_expander('Outcome agencies', expanded=False)
    with agency_expander:
        agencydf = data_functions.inout_agencies_data_prep(iodf, date_for_comp='out')
        plot_functions.inout_agency_bar_plot(agencydf, date_for_comp='out')

    # BREED EXPANDER
    breed_expander = st.beta_expander('Outcome breeds', expanded=False)
    with breed_expander:
        breeddf = data_functions.inout_breed_data_prep(iodf, start_month, end_month, date_for_comp='out')

        breed1, sp, breed2 = st.beta_columns((.25,.02,1))
        species = breed1.selectbox(label='Choose an animal type',
                                   options=sorted(breeddf.type.unique().tolist()),
                                   index=0,
                                   key='breeds')

        breed1.write("<br>", unsafe_allow_html=True)

        max_base = breed1.radio(label='Popular breeds based on:',
                                options=['Full History','Latest Month'],
                                index=0,
                                key='breeds')
        max_base_dict = {'Full History':'history', 'Latest Month':'latest'}

        breed1.write("<br>", unsafe_allow_html=True)

        perc = breed1.checkbox(label='Show values as % of total animals',
                               value=False,
                               key='breeds')

        breed_fig = plot_functions.inout_breed_line_plot(breeddf, species, perc=perc, max_base=max_base_dict[max_base],
                                                         date_for_comp='out')

        breed2.plotly_chart(breed_fig, use_container_width=True)

    # AGE EXPANDER
    age_expander = st.beta_expander('Outcome ages', expanded=False)
    with age_expander:
        agedf = data_functions.inout_age_data_prep(iodf, start_month, end_month, AGE_GROUPS, date_for_comp='out')

        age1, sp, age2 = st.beta_columns((.25, .02, 1))
        species_age = age1.selectbox(label='Choose an animal type',
                                 options=sorted(breeddf.type.unique().tolist()),
                                 index=0,
                                 key='age')

        age1.write("<br>", unsafe_allow_html=True)

        max_base_age = age1.radio(label='Popular ages based on:',
                              options=['Full History', 'Latest Month'],
                              index=0,
                              key='age')

        age1.write("<br>", unsafe_allow_html=True)

        perc_age = age1.checkbox(label='Show values as % of total animals',
                             value=False,
                             key='age')

        age_fig = plot_functions.inout_age_line_plot(agedf, species_age, AGE_GROUPS, perc=perc_age,
                                                      max_base=max_base_dict[max_base_age], date_for_comp='out')

        age2.plotly_chart(age_fig, use_container_width=True)

# -----------------------------------------------
# 4th: Fostering page
def fostering_page():
    st.title('Fostering')

# -----------------------------------------------
# 5th: General summary page
def geography_page():
    st.title('Geography of rescues')

# -----------------------------------------------
# 6th: General summary page
def events_page():
    st.title('Marketing & events')

# -----------------------------------------------
# 7th: General summary page
def staffing_page():
    st.title('Staffing')

# -----------------------------------------------
# 8th: General summary page
def resources_page():
    st.title('Resources')

# -----------------------------------------------
# 0th: Notes page
def notes_page():
    st.title('Notes')

    st.write("<br>Note: This is a very rough first draft using fake (and unrealistic) data. For now, "
             "only General Summary, Intakes, and Outcomes pages have information. Also, I have not written any "
             "explanations for the plots/how to interpret them yet, but I will!", unsafe_allow_html=True)
    st.subheader("Structural Changes")
    st.write('&nbsp1. First tab can be information on animal shelters/animal issues in the shelter\'s community.<br>'
             '&nbsp2. Maybe combine information on fostering, staffing, and monetary contributions under Resources.<br>'
             '&nbsp3. Add information on costs.<br>'
             '&nbsp4. Have a separate section just for adoption outcomes?<br>'
             '&nbsp5. Figure out other issues/problems animal shelters are trying to solve.',
             unsafe_allow_html=True)
    st.subheader("Using This App")
    st.write(
        '&nbsp1. Every plot is interactive, and you can click on the legends to filter the data shown on the plot.<br>'
        '&nbsp2. Sections enclosed by a box can be expanded (click the + sign) or minimized (click the - sign).<br>'
        '&nbsp3. Data will be updated based on the user inputs in the left-hand side.',
        unsafe_allow_html=True)


# -----------------------------------------------
# Call each page
def create_app_with_pages():
    app = MultiApp()
    app.add_app('Notes', notes_page, [])
    app.add_app("General Summary", general_page, [iodf])
    app.add_app("Intakes", intake_page, [iodf, INTAKE_MAPPING])
    app.add_app("Outcomes", outcome_page, [iodf])
    app.add_app("Fostering", fostering_page, [])
    app.add_app("Geography of Rescues", geography_page, [])
    app.add_app("Marketing & Events", events_page, [])
    app.add_app("Staffing", staffing_page, [])
    app.add_app("Resources", resources_page, [])
    app.run(logo_path="fake_logo.png")

if __name__ == '__main__':
    create_app_with_pages()