import sys
import os
from datetime import datetime
import pandas as pd

from PyQt5.QtGui import (QIcon, QRegExpValidator, QIcon)
from PyQt5.QtCore import Qt, QRegExp, QSortFilterProxyModel, QAbstractTableModel
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QLineEdit, QAction, QMainWindow,
                             QWidget, QLabel, QTableView, QPushButton,
                             QFormLayout, QMessageBox, QHeaderView, QFileDialog, QDialog)

class Login(QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.setWindowTitle('Immulite Allergen Scanning')
        self.setWindowIcon(QIcon('app.ico'))
        self.resize(320, 120)

        layout = QFormLayout()

        self.text_name = QLineEdit(self)
        self.text_name.setStyleSheet('font-size: 10pt')
        name_label = QLabel("Username")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet('font-size: 10pt;')
        layout.addRow(name_label, self.text_name)

        self.text_pass = QLineEdit(self)
        self.text_pass.setStyleSheet('font-size: 10pt')
        pass_label = QLabel("Password")
        pass_label.setAlignment(Qt.AlignCenter)
        pass_label.setStyleSheet('font-size: 10pt;')
        layout.addRow(pass_label, self.text_pass)

        button_login = QPushButton('Login', self)
        button_login.setStyleSheet('font-size: 10pt;')
        button_login.clicked.connect(self.createConnection)
        layout.addWidget(button_login)
        
        self.setLayout(layout)
        self.show()

    def createConnection(self):
        if self.text_pass.text() in ('PASSWORD'):
            
            # set username for app instance
            global app_instance_username
            app_instance_username = self.text_name.text()

            # sets dialog box response to accepted
            self.accept()

            # set global variable for connection to database
            global db
            db = QSqlDatabase.addDatabase("QPSQL")
            db.setHostName("localhost")
            db.setDatabaseName("DB_NAME")
            db.setUserName("USERNAME")
            db.setPassword("PASSWORD")
            
            if not db.open():
                QMessageBox.critical(
                    None, "Database Connection Error!", "There was an error connecting to the database.\nDatabase Error: {}.".format(db.lastError().databaseText())
                    )
                return False
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')
            
        return True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Immulite Allergen Scanning')
        self.setWindowIcon(QIcon('app.ico'))
        self.resize(800, 500)
        self.layout = QFormLayout()

        # action to open database viewing window
        viewdb_action = QAction("Database", self)
        viewdb_action.triggered.connect(self.open_database_window)

        # action to open database viewing window
        viewexp_action = QAction("Expiring Allergens", self)
        viewexp_action.triggered.connect(self.open_expiring_window)

        # action to open add/remove allergen window
        addallergen_action = QAction("Add Allergen", self)
        addallergen_action.triggered.connect(self.open_add_allergen_window)
        
        # action to save ordering list
        generate_order_action = QAction("Export Order List CSV", self)
        generate_order_action.triggered.connect(self.generate_order_list_csv)

        # action to open window to scan items out of database when loading immulite
        load_immulite_action = QAction("Load Immulite", self)
        load_immulite_action.triggered.connect(self.open_load_immulite)

        # menubar
        self.menuBar = self.menuBar()
        viewdbmenu = self.menuBar.addMenu('View')
        addremovemenu = self.menuBar.addMenu('Add Allergen')
        orderlistmenu = self.menuBar.addMenu('Ordering')
        loadImmuliteMenu = self.menuBar.addMenu('Load Immulite')

        # connect actions to menu options
        viewdbmenu.addAction(viewdb_action)
        viewdbmenu.addAction(viewexp_action)
        addremovemenu.addAction(addallergen_action)
        orderlistmenu.addAction(generate_order_action)
        loadImmuliteMenu.addAction(load_immulite_action)

        # get list of approved allergens
        self.allergens = self.get_allergen_list()

        # create list for adding scanned barcodes to txt file log
        self.scan_log = list()

        # create list for adding scanned barcodes to txt file log
        self.scan_display = list()

        # Text telling user what window is used for
        directions = QLabel("This window is for scanning the barcodes of RECEIVED allergens INTO the database")
        directions.setStyleSheet('font-size: 12pt;')
        directions.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(directions)    

        #  add barcode widget
        self.barcode = QLineEdit()
        self.barcode.setStyleSheet('font-size: 11pt;')
        self.barcode.setPlaceholderText("Scan barcode here")
        self.barcode.textChanged.connect(self.has_comma)
        self.layout.addRow(self.barcode)

        # add pushbutton
        display_scanned_items = QPushButton("Display Scanned Items", self)
        display_scanned_items.setStyleSheet('font-size: 10pt;')
        self.layout.addWidget(display_scanned_items)
        display_scanned_items.clicked.connect(self.display_scan_counts)

        # add layout to widget and set as central widget
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)        

    # add close event. write scan_log to log textfile
    def close_event(self, event):
        if len(self.scan_display) > 0:
            today = datetime.today().strftime("%y%m%d_%H%M%S")
            file_name = f'''...../.../{today}_scanlog.csv'''
            with open(file_name, 'w') as file:
                for i in self.scan_log:    
                    file.write("'{}', '{}','{}','{}','{}'\n".format(i[0], i[1], i[2], i[3], i[4]))

            # save counts for all allergens scanned in 
            self.counts.sort_values(by=['index'], inplace=True)
            file_name = f'''..../..../{today}_allergencounts.csv'''
            self.counts.to_csv(file_name, index=False)           
        else:
            pass

    # wait for barcode to have comma
    def has_comma(self):
        if ',' in self.barcode.text():
            if len(self.barcode.text().split(',')[1]) == 6:
                # self.barcode.setUpdatesEnabled(False)
                self.parse_barcode()

    def parse_barcode(self):
        try:
            # check if user used scanner to input text
            self.barcode_text = self.barcode.text()

            self.expiration_date = self.barcode_text.split(',')[1]
            self.expiration_date = datetime.strptime(self.expiration_date, "%y%m%d").date()
            self.expiration_date = self.expiration_date.strftime('%Y-%m-%d')

            self.lot_number = self.barcode_text.split(',')[0]
            
            # get only the allergen name then reset qlineedit text
            self.allergen_id = self.barcode_text.split('L')[0].upper()
            self.barcode.setText('')
        except:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("Error")
            error_msg.setInformativeText(
                'There was an error scanning the barcode or the scanned allergen is not in the database.\nThe barcode was scanned as {}'.format(self.barcode_text))
            error_msg.setWindowTitle("Error")
            error_msg.exec_()
            self.barcode.setText('')

        # check if scanned item is in database
        if self.allergen_id not in self.allergens:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("Error")
            error_msg.setInformativeText(
                'There was an error scanning the barcode or the scanned allergen is not in the database.\nThe barcode was scanned as {}'.format(self.barcode_text))
            error_msg.setWindowTitle("Error")
            error_msg.exec_()
            self.barcode.setText('')

        else:
            try:
                # get tests per tube and current stock
                select_qry_text = ("SELECT current_stock FROM allergen_stock WHERE id = '{}'").format(
                    self.allergen_id)
                query = QSqlQuery()
                query.exec(select_qry_text)
                while query.next():
                    stock = query.value(0)
                # calc new stock
                stock += 1

                # update stock
                update_qry_text = ("UPDATE allergen_stock SET current_stock = {} WHERE id = '{}'").format(
                    stock, self.allergen_id)
                query.exec(update_qry_text)

                # add tube to allergen_list table
                insert_qry_text = ("INSERT INTO allergen_list VALUES ('{}', '{}', '{}', '{}')".format(
                    self.allergen_id,
                    self.lot_number,
                    self.expiration_date,
                    datetime.now()
                ))
                query.exec(insert_qry_text)

                # append scanned item to lists
                self.scan_log.append([app_instance_username, self.allergen_id, self.lot_number, self.expiration_date, datetime.now()])
                self.scan_display.append(self.allergen_id)

            except:
                QMessageBox.critical(None,
                "QTableView Example - Error!",
                "Database Error: %s \n The database could not be updated. " % db.lastError())

    def display_scan_counts(self):
        # this try/except checks if the QTableView widget is already displayed and removes it then adds the updated widget.
        try:
            self.layout.removeWidget(self.view)
            self.view.deleteLater()
            self.view = None
        except:
            pass

        # creates dataframe object from the list of scanned items
        df = pd.DataFrame(self.scan_display, columns=['count'])
        self.counts = pd.DataFrame(df['count'].value_counts().reset_index())

        # calls the qabstracttablemodel and creates a qtableview widget with the dataframe created above.
        model = dataFrameModel(self.counts)
        self.view = QTableView()
        self.view.setModel(model)
        self.view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.view)
        
    def get_allergen_list(self):
        # get allergens from sql db
        try:
            qry_text = "SELECT id FROM allergen_stock"
            query = QSqlQuery()
            query.exec(qry_text)
            allergens = []
            while query.next():
                allergens.append(query.value(0))
        except:
            QMessageBox.about(self, 'Connection', 'Database failure.')
        return allergens

    def get_expiring_allergens(self):
        # get allergens from sql db
        try:
            qry_text = "SELECT * FROM allergen_list"
            query = QSqlQuery()
            query.exec(qry_text)
            allergens = []
            while query.next():
                allergens.append(query.value(0))
        except:
            QMessageBox.about(self, 'Connection', 'Database failure.')
        return allergens

    def generate_order_list_csv(self):
        # query sql db to get allergens below threshold
        try:
            qry_text = "SELECT id, catalog_number, order_quantity FROM allergen_stock WHERE current_stock < minimum_tubes"
            query = QSqlQuery()
            query.exec(qry_text)
            order_list = []

            while query.next(): # iterate through query and add to list
                order_list.append([query.value(0), query.value(1), query.value(2)])

            df = pd.DataFrame(order_list, columns=['id', 'catalog number', 'order quantity']) # convert to dataframe for easy saving to csv
            
        except:
            QMessageBox.about(self, 'Connection', 'Database failure.')
        
        # save file
        file_name = QFileDialog.getSaveFileName(self, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if len(file_name[0]) > 0:
            file = open(file_name[0], 'w')
            file.write(df.to_csv(index=False, header=False, line_terminator='\n'))
            file.close()

    def open_expiring_window(self):
        self.eUI = ExpiringUI()
        self.eUI.show()

    def open_database_window(self):
        self.dUI = DatabaseUI()
        self.dUI.show()

    def open_add_allergen_window(self):
        self.aUI = AddAllergenUI()
        self.aUI.show()

    def open_load_immulite(self):
        self.lUI = LoadImmuliteUI()
        self.lUI.show()

class ExpiringUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Expiring Allergens')
        self.setWindowIcon(QIcon('app.ico'))
        self.resize(650, 500)
        self.layout = QFormLayout()

        # check for expiring allergens
        self.expiring_allergen_list = self.openEvent()
            
        # display expiring allergens if there are any
        if len(self.expiring_allergen_list) > 0:

            # creates dataframe object from the list of scanned items
            df = pd.DataFrame(self.expiring_allergen_list, columns=['ID', 'Lot', 'Expiration Date'])

            # calls the qabstracttablemodel and creates a qtableview widget with the dataframe created above.
            model = dataFrameModel(df)
            self.view = QTableView()
            self.view.setModel(model)
            self.view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.layout.addWidget(self.view)

            self.button = QPushButton("Remove expired allergens", self)
            self.button.setStyleSheet('''background:#34d8eb;
            font-size: 15px;''')
            self.layout.addWidget(self.button)
            self.button.clicked.connect(self.RemoveExpiredAllergens)

            # add layout 
            self.setLayout(self.layout)
            self.show()

        else:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("")
            error_msg.setInformativeText(
                'There are no allergens expired or expiring soon.')
            error_msg.setWindowTitle("No expired allergens")
            error_msg.exec_()

    def RemoveExpiredAllergens(self):
        try:
            query = QSqlQuery()
            qry_text = "DELETE FROM allergen_list WHERE expiration_date < NOW()"
            query.exec(qry_text)
            QMessageBox.about(self, 'Connection', 'Expired allergens removed from database.')
            self.close()
        except:
            QMessageBox.critical(None, 
            "Update Database Error!",
            "Database Error: {} \n The database could not be updated.".format(db.lastError()))

    def openEvent(self):
        try:
            expiring_allergens_list = []
            # get tests per tube and current stock
            expire_qry_text = "SELECT * FROM allergen_list WHERE expiration_date < NOW() + INTERVAL '1 MONTH' ORDER BY expiration_date ASC"
            query = QSqlQuery()
            query.exec(expire_qry_text)
            while query.next():
                tube_id = query.value(0)
                tube_lot = query.value(1)
                tube_expires = query.value(2)
                tube_expires = tube_expires.toString()
                expiring_allergens_list.append([tube_id, tube_lot, tube_expires])
            return expiring_allergens_list
        except:
             QMessageBox.critical(None, 
            "Database Error!",
            "Database Error: {} \n Expired allergens could not be retrieved from database.".format(db.lastError()))

class DatabaseUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setWindowTitle('View/Edit Database')
        self.setWindowIcon(QIcon('app.ico'))
        self.resize(1200, 800)

        # Set up sqltablemodel
        self.model = QSqlTableModel(self)
        self.model.setTable('allergen_stock')
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit) # YOU NEED A PRIMARY KEY SET IN YOUR SQL DATABASE TO SAVE CHANGES IN A QSQLTABLEMODEL
        self.model.setHeaderData(0, Qt.Horizontal, "id")
        self.model.setHeaderData(1, Qt.Horizontal, "catalog number")
        self.model.setHeaderData(2, Qt.Horizontal, "current stock")
        self.model.setHeaderData(3, Qt.Horizontal, "order quantity")
        self.model.setHeaderData(4, Qt.Horizontal, "minimum tubes")
        self.model.select()

        # set up filtering model
        filter_proxy_model = QSortFilterProxyModel()
        filter_proxy_model.setSourceModel(self.model)
        filter_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        filter_proxy_model.setFilterKeyColumn(0)

        # search filter
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Filter table using id column (e.g. F95)")
        self.search_filter.setStyleSheet('font-size: 20px;')
        self.search_filter.textChanged.connect(
            filter_proxy_model.setFilterRegExp)
        self.layout.addWidget(self.search_filter)

        # create table view
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.resizeColumnsToContents()
        # filter model
        self.view.setModel(filter_proxy_model)
        self.view.setSortingEnabled(True)
        # have columns span entire window
        self.view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # set layout
        self.layout.addWidget(self.view)

        # push button to save changes to database
        self.save_db_button = QPushButton("Save Changes", self)
        self.save_db_button.clicked.connect(self.submit)
        self.save_db_button.setStyleSheet('''background:#34d8eb;
                                          font-size: 15px;''')

        self.layout.addWidget(self.save_db_button)
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def submit(self):
        try:
            self.model.submitAll()  # submitAll() is only for sqltablemodel
            QMessageBox.about(self, 'Connection', 'Database Updated')
        except :
            QMessageBox.about(self, 'Connection', 'Failed To Update Database')

class LoadImmuliteUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Immulite Allergen Scanning')
        self.setWindowIcon(QIcon('app.ico'))
        self.resize(650, 400)
        self.layout = QFormLayout()

        # get list of approved allergens
        self.allergens = self.get_allergen_list()

        # Text telling user what window is used for
        directions = QLabel("Scan the barcodes of allergens loaded onto the Immulites here")
        directions.setStyleSheet('font-size: 12pt;')
        self.layout.addWidget(directions)

        #  add barcode widget
        self.barcode = QLineEdit()
        self.barcode.setPlaceholderText("Scan barcode here")
        self.barcode.setStyleSheet('font-size: 10pt')
        self.barcode.textChanged.connect(self.has_comma)
        self.layout.addRow( self.barcode)

        # add pushbutton
        self.scan_display = list()
        display_scanned_items = QPushButton("Display Scanned Items", self)
        display_scanned_items.setStyleSheet('font-size: 10pt;')
        self.layout.addWidget(display_scanned_items)
        display_scanned_items.clicked.connect(self.display_scan_counts)

        # add layout 
        self.setLayout(self.layout)
        self.show()

    # wait for barcode to have comma
    def has_comma(self):
        if ',' in self.barcode.text():
            if len(self.barcode.text().split(',')[1]) == 6:
                # self.barcode.setUpdatesEnabled(False)
                self.parse_barcode()

    def parse_barcode(self):
        # check if user used scanner to input text
        self.allergen_id = self.barcode.text()

        self.expiration_date = self.allergen_id.split(',')[1]
        self.expiration_date = datetime.strptime(self.expiration_date, "%y%m%d").date()
        
        self.lot_number = self.allergen_id.split(',')[0]
        
        # get only the allergen name then reset qlineedit text
        self.allergen_id = self.allergen_id.split('L')[0].upper()
        self.barcode.setText('')

        # append allergen id to scan_display list
        self.scan_display.append(self.allergen_id)

        # check if scanned item is in database
        if self.allergen_id not in self.allergens:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("Error")
            error_msg.setInformativeText(
                'There was an error scanning the barcode or the scanned allergen is not in the database.\nThe barcode was scanned as {}'.format(self.barcode.text()))
            error_msg.setWindowTitle("Error")
            error_msg.exec_()
            self.barcode.setText('')

        else:
            try:
                # remove allergen tube from allergen_list table
                query = QSqlQuery()
                update_qry_text = f"""DELETE FROM allergen_list al
                                    WHERE al.lot = '{self.lot_number}' AND
                                    al.date_scanned = (SELECT MAX(al2.date_scanned)
                                    FROM allergen_list al2
                                    WHERE al2.id = al.id and al2.lot = al.lot and al2.expiration_date = al.expiration_date
                                    );"""
                query.exec(update_qry_text)

                # get tests per tube and current stock
                select_qry_text = ("SELECT current_stock FROM allergen_stock WHERE id = '{}'").format(
                    self.allergen_id)
                query = QSqlQuery()
                query.exec(select_qry_text)
                while query.next():
                    stock = query.value(0)
                # calc new stock
                stock -= 1

                # update stock
                update_qry_text = ("UPDATE allergen_stock SET current_stock = {} WHERE id = '{}'").format(
                    stock, self.allergen_id)
                query.exec(update_qry_text)

            except:
                QMessageBox.critical(None,
                "QTableView Example - Error!",
                "Database Error: %s \n The database could not be updated. " % db.lastError())
        
    def get_allergen_list(self):
        # get allergens from sql db
        try:
            qry_text = "SELECT id FROM allergen_stock"
            query = QSqlQuery()
            query.exec(qry_text)
            allergens = []
            while query.next():
                allergens.append(query.value(0))
        except:
            QMessageBox.about(self, 'Connection', 'Database failure.')
        return allergens

    def display_scan_counts(self):
        # this try/except checks if the QTableView widget is already displayed and removes it then adds the updated widget.
        try:
            self.layout.removeWidget(self.view)
            self.view.deleteLater()
            self.view = None
        except:
            pass

        # creates dataframe object from the list of scanned items
        df = pd.DataFrame(self.scan_display, columns=['count'])
        counts = pd.DataFrame(df['count'].value_counts().reset_index())

        # calls the qabstracttablemodel and creates a qtableview widget with the dataframe created above.
        model = dataFrameModel(counts)
        self.view = QTableView()
        self.view.setModel(model)
        self.view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.view)

class AddAllergenUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Add Allergens')
        self.resize(400, 250)
        self.setWindowIcon(QIcon('app.ico'))
        vbox = QVBoxLayout()

        # validator
        validation_rule_int = QRegExpValidator(QRegExp(r'[0-9]+'))

        # get allergen id
        self.new_allergen_id = QLineEdit(self)
        self.new_allergen_id.setPlaceholderText('Allergen id (e.g. F95)')
        self.new_allergen_id.setStyleSheet('background:white')
        vbox.addWidget(self.new_allergen_id)

        # get catalog number
        self.new_catalog_number = QLineEdit(self)
        self.new_catalog_number.setPlaceholderText('Siemens catalog number')
        self.new_catalog_number.setStyleSheet('background:white')
        self.new_catalog_number.setValidator(validation_rule_int)
        vbox.addWidget(self.new_catalog_number)

        # get current stock
        self.current_stock = QLineEdit(self)
        self.current_stock.setPlaceholderText('Current number of tubes')
        self.current_stock.setStyleSheet('background:white')
        self.current_stock.setValidator(validation_rule_int)
        vbox.addWidget(self.current_stock)

        # get minumum tubes - when to order
        self.when_to_order = QLineEdit(self)
        self.when_to_order.setPlaceholderText('Minimum tubes on hand (will order when LESS THAN this number)')
        self.when_to_order.setStyleSheet('background:white')
        self.when_to_order.setValidator(validation_rule_int)
        vbox.addWidget(self.when_to_order)

        # get order quantity - when to order
        self.order_quantity = QLineEdit(self)
        self.order_quantity.setPlaceholderText('Number of tubes to order')
        self.order_quantity.setStyleSheet('background:white')
        self.order_quantity.setValidator(validation_rule_int)
        vbox.addWidget(self.order_quantity)

        self.button = QPushButton("Insert Data", self)
        self.button.setStyleSheet('''background:#34d8eb;
        font-size: 15px;''')

        vbox.addWidget(self.button)
        self.button.clicked.connect(self.insert_allergen)

        self.setLayout(vbox)
        self.show()


    def insert_allergen(self):
        try:
            query = QSqlQuery()
            qry_text = f"""INSERT INTO allergen_stock (id, catalog_number, current_stock, order_quantity, minimum_tubes) VALUES (
                '{self.new_allergen_id.text()}', '{self.new_catalog_number.text()}', '{self.current_stock.text()}', '{self.order_quantity.text()}', '{self.when_to_order.text()}')"""
            query.exec(qry_text)
            QMessageBox.about(self, 'Connection', 'Allergen added to database.')
            self.close()
        except:
            QMessageBox.critical(None, 
            "Update Database Error!",
            "Database Error: {} \n The database could not be updated.".format(db.lastError()))

class dataFrameModel(QAbstractTableModel):
    # custom qabstracttablemodel to create qtableview from dataframe object

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = Login()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        app.exec_()
