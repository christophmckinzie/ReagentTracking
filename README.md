# Reagent Tracking

Immulite Scanning GUI - created using PyQt5, a python wrapper for Qt applications.\
\
This application is used to scan Immulite reagents received from Seimens into a sql database, display/edit the database and generate a order list for said allergens.\
\
Variable naming needs to be put in accordance with pep8.
 
- Logging into the application only requires the correct password. The user can choose any username. The program only uses the username for creating a log of the items scanned into the database. 
- Scanning the tubes in the main window adds to the tube count for that allergen. It also adds that specific tube to another sql table that contains all tubes on hand, until scanned out. This tube list is used for checking expiring tubes as some allergen tubes are used infrequently.
- When a barcode is scanned the computer enters one character at a time. An example barcode is 'F300L2621,211130'. The program is looking for a ',' while the barcode is being read in then checks if the length of the string after the ',' is equal to six (the expiration data is six characters long). The allergen id is determined by splitting the barcode at the 'L'. 
- The push button bellow the text edit bar (where barcodes are scanned) allows the user to see the counts of each scanned item in the session. If they scanned too many/not enough items or if siemens sent the wrong amount they can check that this way. 
- When an allergen is added onto an Immulite instrument, its barcode needs to be scanned out of the database using the 'load immulite' window. This removes a tube from the allergens count in the database as well as removes it from the allergen_list sql table. 
- The database can be viewed/edited using the 'view' menu and clicking 'database'. Currently, everything is editable. There is a filter option at the top and the columns are sortable. To save the changes you have added you must click the save button at the bottom. The columns are also sortable.
- There is also a 'view expiring allergens' window that displays allergens have expired or ones that will be expiring within a months time. There is a push button to delete those items that have expired. 
- If a new allergen is added to the testing options it can be added to the database using the 'add allergen' window. 
- to export a csv file of allergens with low volume, you can use the 'export csv' window. The csv file contains the catalog number of the allergen and the number of tubes to order. This number to order may change depending on the testing demand for each panel. 

## Important Notice
PyQt5 has a driver issue with both MySQL and Postgresql. qsqlpsql.dll needs libpq.dll from PostgreSQL\9.3\libfolder. Add libpq.dll to C:\...\venv\Lib\site-packages\PyQt5\Qt\bin (I just copied all dll files from PostgreSQL\9.3\libfolder to the Qt\bin.). This seems to get PyQt5 working for Postgresql, but to get it to work for MySQL more tinkering was required.
