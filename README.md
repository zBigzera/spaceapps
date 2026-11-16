# Earth System Trend Detective

Tooling to track trends and flood risk through NASA Earht Data this software uses Ordinary Least Squares (OLS), Mann-Kendall, and trend analysis to investigate statistically significant environmental changes that may influence flood occurencies. It integrates NASA Earth science data to analyze long-term trends in precipitation, soil moisture, evapotranspiration, and atmospheric conditions. Rather than examining rainfall independently, the platform evaluates interactions between atmospheric water input and terrestrial water storage to identify changes in flood susceptibility. Historical data are retrieved through NASA POWER, primarily using MERRA-2 reanalysis. The application calculates accumulated rainfall, antecedent precipitation, soil wetness, and compound conditions involving heavy rainfall and elevated soil moisture. By integrating NASA Earth science data, hydrological indicators, and statistical methods, Earth Science Data Analysis transforms complex environmental datasets into accessible scientific information. The platform aims to support researchers, students, environmental professionals, and local decision-makers in understanding regional environmental changes and identifying conditions that may contribute to flood susceptibility.

### Technology

This use Python to Data Analysis, HTML, Java Script and [NASA Data](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

### Project Demonstration

[https://spaceapps-frontend.vercel.app/ ](https://spaceapps-frontend.vercel.app)

https://youtu.be/hLf3wtUEAxA

## Challenge

Change is always occurring in the Earth’s interconnected environmental system, and when it runs in a consistent direction – rising or falling, increasing or decreasing, thickening or thinning – measured variables reflect it. But a measured Earth science data variable can trend one way in one region and the opposite way in another, even when the same process drives both. The multitude of Earth science data variables makes it difficult to select variables that could indicate change, and to then perform an analysis on the selected variables. Your challenge is to create a tool that can select variables measured by Earth science missions or produced by Earth science models, visualize how they change over time, and determine what is changing, where it is changing, how much it is changing, and if these changes are what scientists call “significant.”

### Outline

Summary
Project Demonstration
Project
Project Details
NASA Data
Space Agency Partner & Other Data

See the project documentation
https://www.spaceappschallenge.org/2026/find-a-team/crepusculo1/?tab=project

## Version notes
This pipeline uses long punctual series of NASA POWER 

## Limitations



The spatial and predictive resolution of the proposed analysis could be improved by integrating local environmental data, including Civil Defense alerts, rainfall measurements from pluviometric stations, and river-level measurements from fluviometric stations.

### Future Work

Incorporate a regional monitoring network with stations distributed approximately every 10 km, providing more detailed spatial coverage of rainfall patterns and river-level variations.

Combining these ground-based observations with NASA satellite-derived environmental variables would enable more accurate regional assessments, improved validation of statistical trends, and better identification of localized conditions associated with increased flood susceptibility.

Additionally, historical flood records and Civil Defense notifications could be incorporated to validate the proposed indicators against documented flood events, strengthening the reliability of the analysis and supporting more effective regional early-warning and risk assessment systems.
