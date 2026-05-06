This Kelly_Readme202201019.txt file was generated on 202201027 by Shawn Steidinger

-------------------
GENERAL INFORMATION
-------------------


1. Title of Dataset

	Dataset for: Performance evaluation of the Alphasense OPC-N3 and Plantower PMS5003 sensor in measuring dust events in the Salt Lake Valley, Utah


2. Author Information


  Principal Investigator Contact Information
        Name: Kerry Kelly
           Institution: University of Utah
           Address: MEB3290, Department of Chemical Engineering
           Email:Kerry.kelly@utah.edu


  Associate or Co-investigator Contact Information
        Name: Kamaljeet Kaur
           Institution: University of Utah	
           Address: MEB3290, Department of Chemical Engineering
           Email: kkauruofu@gmail.com


  Alternate Contact Information
           Name: None
           Institution:
           Address:
           Email:


3. Date of data collection (single date, range, approximate date) <suggested format YYYYMMDD> 
	20220401-20220430


4. Geographic location of data collection (where was data collected?): 
	Salt Lake City, UT, USA


5. Information about funding sources that supported the collection of the data: 
	This material is based upon work supported by the National Science Foundation under Grant No. 2012091 Collaborative Research Network Cluster: Dust in the Critical Zone and under Grant No. 2228600  CIVIC-PG: TRACK A: Community Resilience through Engaging, Actionable, Timely, High-Resolution Air Quality Information (CREATE-AQI).


--------------------------
SHARING/ACCESS INFORMATION
-------------------------- 


1. Licenses/restrictions placed on the data: 
	CC BY – Allows other to use and share your data, even commercially, with attribution


2. Links to publications that cite or use the data: 
	Submitted and not published yet


3. Links to other publicly accessible locations of the data: N/A


4. Links/relationships to ancillary data sets: N/A


5. Was data derived from another source? YES
           If yes, list source(s): Part of the data was downloaded from EPA Air Quality Data Site


6. Recommended citation for the data: 
	Kelly, K., Kaur, K. (2022). Dataset for: Performance evaluation of the Alphasense OPC-N3 and Plantower PMS5003 sensor in measuring dust events in the Salt Lake Valley, Utah. The Hive: University of Utah Research Data Repository. https://doi.org/10.7278/S50d-xbns-3ge3


---------------------
DATA & FILE OVERVIEW
---------------------


1. File List
   A. Filename: Data_Set_for_Kaur_AMT_2022.xlsx   
      Short description: Contains sheet labelled as the site name (HW, RS, EQ). Each sheet contains the OPC-N3, PMS5003 sensors, and FEM data. The sheet “PM-ratio based correlation” provided the data used to get the PM-ratio based correlation. The sheets “RS correction using GRIMM ratio”, “RS correction using opc ratio” and “EQ corrected using EQ ratio” contains corrected PMS data, corrected using the PM-ratio method. The sheets also demonstrated the calculation of RMSE (root mean square error) and NRMSE (normalized RMSE)


        
   B. Filename:     NA   
      Short description:        


        
   C. Filename:        NA
      Short description:


2. Relationship between files:   There is only one file     




3. Additional related data collected that was not included in the current data package: None



 
4. Are there multiple versions of the dataset? yes/no No
   If yes, list versions:
           Name of file that was updated:
                     i. Why was the file updated? 
                ii. When was the file updated?
           Name of file that was updated:
                      i. Why was the file updated?
                    ii. When was the file updated?






--------------------------
METHODOLOGICAL INFORMATION
--------------------------


1. Description of methods used for collection/generation of data: 
<Include links or references to publications or other documentation containing experimental design or protocols used in data collection>
The data include ambient air PM10 concentrations which were collected using low-cost sensors. The data from the EPA monitoring sites were downloaded through: https://aqs.epa.gov/aqsweb/airdata/download_files.html


2. Methods for processing the data: <describe how the submitted data were generated from the raw or collected data> The file contained raw data and processed data in excel form


3. Instrument- or software-specific information needed to interpret the data: Microsoft Excel


4. Standards and calibration information, if appropriate: None


5. Environmental/experimental conditions: Ambient Air measurements


6. Describe any quality-assurance procedures performed on the data: The downloaded EPA measurements excluded measurements that were flagged by EPA as potentially erroneous. The measurements corresponding to humidity >85% were also omitted.


7. People involved with sample collection, processing, analysis and/or submission: Kamaljeet Kaur and Kerry Kelly






-----------------------------------------
DATA-SPECIFIC INFORMATION FOR: Data_Set_for_Kaur_AMT_2022.xlsx  
-----------------------------------------
<create sections for each dataset (or file if appropriate) included>

Sheet: HW

1. Number of variables: 13

2. Number of cases/rows: 711

3. Variable List
    A. Name: Date
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    B. Name: Wind Speed (Knots)
       Description: Wind speed reported at HW in units Knots

    C. Name: Wind direction (degree compass)
       Description: Wind direction in unit degree compass

    D. Name: Temp F
       Description: Temperature in Fahrenheit

    E. Name: RH %
       Description: Relative humidity in %

    F. Name: FEM-HW PM2.5/PM10
       Description: Ratio of FEM reported PM2.5 to FEM reported PM10 at HW site

    G. Name: FEM-HW PM2.5 ug/m3
       Description: FEM reported PM2.5 in units ug/m3 at HW station

    H. Name: FEM-HW PM10
       Description: FEM reported PM10 in units ug/m3 at HW station

    I. Name: OPC-HW
       Description: PM10 in ug/m3 measured by Alphasense OPC-N3 at HW site

    J. Name: PMS-HW-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at HW site

    K. Name: PMS-HW-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at HW site

    L. Name: PMS-HW-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at HW site

    M. Name: PMS
       Description: Average PM10 in ug/m3 of PMS-HW-1A, PMS-HW-2A, and PMS-HW-2B

4. Missing data codes:
        Code/symbol blank  
       


5. Specialized formats of other abbreviations used


------------------
Sheet: PM-ratio based Correlation

1. Number of variables: 9

2. Number of cases/rows: 711

3. Variable List
    A. Name: Date
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    B. Name: RH %
       Description: Relative humidity in %

    C. Name: FEM-HW 
       Description: FEM reported PM10 in units ug/m3 at HW station

    D. Name: PMS-HW-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at HW site

    E. Name: PMS-HW-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at HW site

    F. Name: PMS-HW-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at HW site


    G. Name: FEM-HW PM2.5/PM10
       Description: Ratio of FEM reported PM2.5 to FEM reported PM10 at HW site

    H. Name: PMS PM10
       Description: Average PM10 in ug/m3 of PMS-HW-1A, PMS-HW-2A, and PMS-HW-2B

 
    I. Name: FEM-HW PM10
       Description: FEM reported PM10 in units ug/m3 at HW station

  

4. Missing data codes:
        Code/symbol blank  
       


5. Specialized formats of other abbreviations used


-----------------------------------------


Sheet: RS

1. Number of variables: 7

2. Number of cases/rows: 509

3. Variable List
    A. Name: Date
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    B. Name: GRIMM
       Description: GRIMM reported PM10 in ug/m3 at RS site

    C. Name: OPC-RS
       Description: PM10 in ug/m3 measured by Alphasense OPC-N3 at RS site

    D. Name: PMS-RS-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at RS site

    E. Name: PMS-RS-1B
       Description: PM10 in ug/m3 measured by PMS sensor 1 node B at RS site

    F. Name: PMS-RS-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at RS site

    G. Name: PMS-RS-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at RS site


4. Missing data codes:
        Code/symbol blank  
       


5. Specialized formats of other abbreviations used

------------------------------------------------------------------------------------

Sheet: RS Correction using GRIMM ratio

1. Number of variables: 13

2. Number of cases/rows: 304

3. Variable List

    A. Name: Date & Time
       Description: Date in format Month/Date/Year Hour:Min in Mountain Standard Time

    B. Name: Time MDT
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    C. Name: PM10 GRIMM
       Description: GRIMM reported PM10 in ug/m3 at RS site

    D. Name: PM2.5 GRIMM
       Description: GRIMM reported PM2.5 in ug/m3 at RS site

    E. Name: GRIMM PM2.5/PM10
       Description: Ratio of GRIMM reported PM2.5 and PM10 

    G. Name: PMS-RS-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at RS site

    H. Name: PMS-RS-1B
       Description: PM10 in ug/m3 measured by PMS sensor 1 node B at RS site

    I. Name: PMS-RS-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at RS site

    J. Name: PMS-RS-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at RS site

    O. Name: PMS-RS-1A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and GRIMM reported PM ratios for PMS sensor 1 node A

    P. Name: PMS-RS-1B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and GRIMM reported PM ratios for PMS sensor 1 node B

    Q. Name: PMS-RS-2A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and GRIMM reported PM ratios for PMS sensor 2 node A

    R. Name: PMS-RS-2B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and GRIMM reported PM ratios for PMS sensor 2 node B



4. Missing data codes:
        Code/symbol blank  

5. Specialized formats of other abbreviations used

------------------------------------------------------------------------------------

Sheet: RS Correction using opc ration

1. Number of variables: 17

2. Number of cases/rows: 304

3. Variable List

    A. Name: Date & Time
       Description: Date in format Month/Date/Year Hour:Min in Mountain Standard Time

    B. Name: Time MDT
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    C. Name: PM10 GRIMM
       Description: GRIMM reported PM10 in ug/m3 at RS site

    D. Name: PM2.5 GRIMM
       Description: GRIMM reported PM2.5 in ug/m3 at RS site

    E. Name: PM2.5/PM10 GRIMM
       Description: Ratio of GRIMM reported PM2.5 and PM10 

    F. Name: Date and Time
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    G. Name: OPC PM2.5
       Description: OPC reported PM2.5 in ug/m3 at RS site

    H. Name: OPC PM10
       Description: OPC reported PM10 in ug/m3 at RS site

    I. Name: OPC PM ratio
       Description: Ratio of OPC reported PM2.5 and PM10 

    K Name: PMS-RS-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at RS site

    L Name: PMS-RS-1B
       Description: PM10 in ug/m3 measured by PMS sensor 1 node B at RS site

    M Name: PMS-RS-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at RS site

    N Name: PMS-RS-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at RS site

    S. Name: PMS-RS-1A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and OPC reported PM ratios for PMS sensor 1 node A

    T. Name: PMS-RS-1B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and OPC reported PM ratios for PMS sensor 1 node B

    U. Name: PMS-RS-2A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and OPC reported PM ratios for PMS sensor 2 node A

    V. Name: PMS-RS-2B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and OPC reported PM ratios for PMS sensor 2 node B



4. Missing data codes:
        Code/symbol:blank  


5. Specialized formats of other abbreviations used


-----------------------------------------


Sheet: EQ

1. Number of variables: 6

2. Number of cases/rows: 711

3. Variable List
    A. Name: Date
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    B. Name: FEM-EQ PM10
       Description: FEM reported PM10 in ug/m3 at EQ site

    C. Name: PMS-EQ-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at EQ site

    D. Name: PMS-EQ-1B
       Description: PM10 in ug/m3 measured by PMS sensor 1 node B at EQ site

    E. Name: PMS-EQ-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at EQ site

    F. Name: PMS-EQ-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at EQ site


4. Missing data codes:
        Code/symbol:blank  
       


5. Specialized formats of other abbreviations used


-----------------------------------------


Sheet: EQ corrected using EQ ratios

1. Number of variables: 12

2. Number of cases/rows: 721

3. Variable List
    A. Name: Date MDT
       Description: Date in format Month/Date/Year Hour:Min in Mountain Day Time

    B. Name: FEM-EQ PM10
       Description: FEM reported PM10 in ug/m3 at EQ site

    C. Name: FEM-EQ PM2.5
       Description: FEM reported PM2.5 in ug/m3 at EQ site

    D. Name: FEM-EQ PM2.5/PM10
       Description: ratio of FEM reported PM2.5 to PM10 at EQ site

    G. Name: PMS-EQ-1A
       Description: PM10 in ug/m3 measured by PMS sensor 1 node A at EQ site

    H. Name: PMS-EQ-1B
       Description: PM10 in ug/m3 measured by PMS sensor 1 node B at EQ site

    I. Name: PMS-EQ-2A
       Description: PM10 in ug/m3 measured by PMS sensor 2 node A at EQ site

    J. Name: PMS-EQ-2B
       Description: PM10 in ug/m3 measured by PMS sensor 2 node B at EQ site

    O. Name: PMS-EQ-1A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and FEM-EQ reported PM ratios for sensor 1 node A


    P. Name: PMS-EQ-1B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and FEM-EQ reported PM ratios for sensor 1 node B

    Q. Name: PMS-EQ-2A-C
       Description: Corrected PM10 in ug/m3 using the correction factor and FEM-EQ reported PM ratios for sensor 2 node A

    R. Name: PMS-EQ-2B-C
       Description: Corrected PM10 in ug/m3 using the correction factor and FEM-EQ reported PM ratios for sensor 2 node B


4. Missing data codes:
        Code/symbol:blank  
       


5. Specialized formats of other abbreviations used








