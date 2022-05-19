#!/usr/bin/python3
''' main.py
This script is just an example of a desktop application to exploit a relational database containing data on
customer and products (a kind of oversimplified Customer Relationship Management (CRM).

It is implemented to evaluate the use of tkinter to support windows interaction with regard to other solutions
based on framworks for implementing back-end web applications..

The solution implemented use a structured approach, where a set of functions are defined to perform the functionalities
requested.
'''

import tkinter
from tkinter import ttk, messagebox
import sqlite3
import matplotlib.pyplot as plt
from PIL import ImageTk

def index(indexWin):
    '''
    index function is used to set-up on the index window the initial form to collect identification data.
    :param indexWin: the window where the form widgets are placed
    :return: none
    '''
    # the name introduced will be placed in userId
    userId = tkinter.StringVar(indexWin)
    # add label with admin/customer/supplier
    acsLabel = ttk.Label(indexWin, text='Please identify supplier/customer/admin', font=('Arial', 20))
    lastRow = 0
    acsLabel.grid(row=lastRow)
    # add label identification
    idLabel = ttk.Label(indexWin, text='Identification:', font=('Arial', 8))
    lastRow += 1
    idLabel.grid(row=lastRow)
    # add entry box for data
    entryId = ttk.Entry(width=20, textvariable=userId)
    lastRow += 1
    entryId.grid(row=lastRow)
    # add submit button
    submitButton = ttk.Button(indexWin, text='Display data', command=lambda: identify(userId.get(), indexWin))
    lastRow += 1
    submitButton.grid(row=lastRow)
    # add reset button
    resetButton = ttk.Button(indexWin, text='Reset data', command=lambda: userId.set(''))
    lastRow += 1
    resetButton.grid(row=lastRow)
    return

def identify(userId, rootWin):
    '''
    identify verifies the user identification passed and triggers the action to show the related data, which depend on
     the type of user.
    :param userId: the user identification
    :param rootWin: the root window of the application
    :return: none
    '''
    userRegister, userType = getUserData(userId)
    if userType == 'A':
        return makeAdminPage(rootWin)
    elif userType == 'P':
        return makeSupplierPage(userRegister, rootWin)
    elif userType == 'C':
        return makeCustomerPage(userRegister, rootWin)
    else:
        return makeErrorPage(userId, rootWin)

def hbarsPlot (pltData, pltTitle, pltXlabel, pltYlable, fileName):
    '''
    hbarsPlot plots a simple horizontal bar chart with data passed
    :param pltData: a dictionary with keys (in y) and values (in x)
    :param pltTitle: title of the figure
    :param pltXlabel: the label for y
    :param pltYlable: the lable for x
    :param fileName: the name of the file to save the figure
    :return:
    '''
    plt.clf()
    plt.title(pltTitle)
    plt.xlabel(pltXlabel)
    plt.ylabel(pltYlable)
    plt.barh(list(pltData.keys()), list(pltData.values()))
    plt.savefig('img/' + fileName)

def getPeriod():
    '''
    Gets the initial and final date of the period activities in the BD
    :return: initial and final date
    '''
    dbConexion = sqlite3.connect('data.db')
    cursor = dbConexion.cursor()
    cursor.execute('SELECT MIN(date) FROM activity')
    initial = cursor.fetchone()
    cursor.execute('SELECT MAX(date) FROM activity')
    final = cursor.fetchone()
    dbConexion.close()
    return initial[0], final[0]

def queryActivity(user, inout):
    '''
    Performs the query on the DB extracting all products having activity (in or out) in the period, and it cost or price.
    :param user: the user identification
    :param inout: the activity movements to be computed: "C" (inputs), "V" (outputs)
    :return: a list of registers, each one containing the product name and cost or price
    '''
    dbConexion = sqlite3.connect('data.db')
    cursor = dbConexion.cursor()
    query = 'SELECT products.name, activity.price FROM products, activity WHERE activity.idproduct = products.id'
    if len(inout) != 0:
        query += ' AND activity.inout = "' + inout + '"'
    if len(user) != 0:
        query = query + ' AND activity.idsuppocust = "' + user + '"'
    cursor.execute(query)
    allActs = cursor.fetchall()
    dbConexion.close()
    return allActs

def makeAdminPage(rootWin):
    '''
    makeAdminPage collects data related to all sales and purchases registered in the BD, and builds a data page to be
    presented in a pop-up window
    :param rootWin the root window from where the pop-up will be created
    :return: none
    '''
    # put in a dictionary the sales per product during current period and plot them
    dicData = getValues('V')
    hbarsPlot(dicData, 'Sales per product', 'Sales', 'Product', 'graph-admin-sales.jpg')
    # compute the total amount of sales
    totalSales = 0
    for product, price in dicData.items():
        totalSales += price
    # put in a dictionary the accumulated outputs for each product and generate the graph
    dicData = getActivity('', 'V')
    hbarsPlot(dicData, 'Units sold', 'Units', 'Product', 'graph-admin-units-sold.jpg')
    # put in a dictionary the accumulated inputs for each product and compute balance
    balance = getActivity('', 'C')
    # compute the net balance of inventory
    for product, cant in dicData.items():
        if product in balance:
            balance[product] = balance[product] - cant
        else:
            balance[product] = -cant
    # plot balance
    hbarsPlot(balance, 'Product balance', 'Outputs minus inputs', 'Product', 'graph-admin-inventory.jpg')
    initialDate, finalDate = getPeriod()
    # compute alerts of products below minimum level and display data in a pop-up window
    return displayAdmin(rootWin, initialDate, finalDate, totalSales, stockAlert(balance))

def makeSupplierPage(regCoP, rootWin):
    '''
    makeSupplierPage collects data on all supplies from the BD for a given supplier and builds a pop-up window
    to show them.
    :param regCoP: a register with the supplier identification data
    :param rootWin the root window from where the pop-up will be created
    :return: none
    '''
    # the register to keep data of the client or supplier
    # put in a dictionary the supplies per product during period and plot them
    supplies = getActivity(regCoP[0], 'C')
    hbarsPlot(supplies, 'Supplies per product', 'Supply', 'Product', 'graph-supplier.jpg')
    initialDate, finalDate = getPeriod()
    return displaySoC(rootWin, 'Supplier data', regCoP, initialDate, finalDate, "img/graph-supplier.jpg")

def makeCustomerPage(regCoP, rootWin):
    '''
    makeCustomerPage collects data on all sales from the BD to a given customer and builds a web page to show them.
    :param regCoP: a register with the customer identification data
    :param rootWin the root window from where the pop-up will be created
    :return: none
    '''
    # put in a dictionary the sales per product during period and plot them
    sales = getActivity(regCoP[0], 'V')
    hbarsPlot(sales, 'Sales per product', 'Sales', 'Product', 'graph-customer.jpg')
    initialDate, finalDate = getPeriod()
    return displaySoC(rootWin, 'Customer data', regCoP, initialDate, finalDate, "img/graph-customer.jpg")

def makeErrorPage(userId, rootWin):
    '''
    makeErrorPage configures a pop-up window with the error message
    Note: it is configured to allow further insertion of additional data.
    :param userId: the unknown user identification
    :param rootWin the root window from where the pop-up will be created
    :return: none
    '''
    # set up a pop-up window and a frame inside it to place all these data
    popupWin = tkinter.Toplevel(rootWin)
    popupWin.title('Error')
    frameWin = createScrollableFrame(popupWin)
    # add label with error
    labelError = ttk.Label(frameWin, text='Unknown user ' + userId)
    lastRow = 0
    labelError.grid(column=0, row=lastRow)
    return

def stockAlert(balance):
    '''
    stckAlert computes the current amount of existences for each product and determines if its level is below the
    minimum requested. In this case, an alert flag is raised for the product.
    :param balance: a dictionary with the net amount of inputs minus outputs for each product during the current period
    :return: the list of products below the alert level
    '''
    dbConexion = sqlite3.connect('data.db')
    cursor = dbConexion.cursor()
    query = 'SELECT name, initialstock, minimumstock, location FROM products'
    cursor.execute(query)
    regProd= cursor.fetchall()
    dbConexion.close()
    # update balance of the period with the initial stock
    for reg in regProd:
        product = reg[0]
        if product in balance:
            balance[product] = balance[product] + reg[1]
        else:
            balance[product] = reg[1]
    # make a list with the products being below the minimum stock
    productsBelowLevel = []
    for reg in regProd:
        name = reg[0]
        min = reg[2]
        if name in balance:
            stock = balance[name]
            if stock < min:
                productsBelowLevel.append([name, reg[3], min, stock])
    return productsBelowLevel

def getUserData(identification):
    '''
    getUserData checks if the given identification is correct, and returns the type of user it is and the existing data.
    #TODO verify if the given password is correcto or not
    :param identification: the user identification
    :return: the user register and type -"A" (if Administrator), "C" (if Customer), "P" (if suPplier)-
    '''
    userData = []
    userType = 'A'
    if identification == 'admin':
        return userData, userType
    # get user data from the DB
    dbConexion = sqlite3.connect('data.db')
    cursor = dbConexion.cursor()
    # check if it is a customer
    cursor.execute('SELECT * FROM customers WHERE id = "' + identification + '"')
    userData = cursor.fetchone()
    if userData != None and userData[0] == identification:
        userType = 'C'      # it is customer
    else:
        # check if it is a supplier
        cursor.execute('SELECT * FROM suppliers WHERE id = "' + identification + '"')
        userData = cursor.fetchone()
        if userData != None and userData[0] == identification:
            userType = 'P'  # it is supplier
        else:
            userType = 'E'  # identification is not valid
    dbConexion.close()
    return userData, userType

def getActivity(user, inout):
    '''
    getActivity computes the number of inputs or outputs for the existing products for a given user.
    :param user: the user identification
    :param inout: the activity movements to be computed: "C" (inputs), "V" (outputs)
    :return: a dictionary
    '''
    # get the requested inputs and/or outputs for the given user (if any)
    allActs = queryActivity(user, inout)
    # put in a dictionary products and total amount of units
    actProduct = {}
    for reg in allActs:
        # get product name and update counters in the dictionary
        product = reg[0]
        if product in actProduct:
            actProduct[product] = actProduct[product] + 1
        else:
            actProduct[product] = 1
    return actProduct

def getValues(inout):
    '''
    getValues computes the value of sales or purchases of each product for the period
    :param inout: the movements to be computed: "C" (inputs), "V" (outputs)
    :return: a dictionary with accumulated price values of each product for the period
    '''
    # get the requested inputs or outputs
    allActs = queryActivity('', inout)
    # a dictionary to accumulate amounts
    actProduct = {}
    for reg in allActs:
        # product name is in col 0 and price in col 1
        product = reg[0]
        if product in actProduct:
            actProduct[product] = actProduct[product] + reg[1]
        else:
            actProduct[product] = reg[1]
    return actProduct

def displayAdmin(rootWin, initialDate, finalDate, totalSales, alerts):
    '''
    It displays admin data passed in a pop-up window which is created from the root window
    :param rootWin: the root window where the pop-up will be created
    :param initialDate: the initial date of the period
    :param finalDate: the final date of the period
    :param totalSales: the total amount of sales in the period
    :param alerts: the list of alerts for the stocks
    :return: none
    '''
    # set up a pop-up window and a frame inside it to place all these data
    popupWin = tkinter.Toplevel(rootWin)
    popupWin.title('Admin data')
    frameWin = createScrollableFrame(popupWin)
    # add label with dates
    labelDates = ttk.Label(frameWin, text='Period from ' + initialDate + ' to ' + finalDate)
    labelDates.grid(column=0, row=0)
    # add label with sales plot
    # Image objects are declared global to avoid being erased when this function finish because they shall be 'alive'
    # when the window will be displyed
    global imgSales
    imgSales = ImageTk.PhotoImage(file="img/graph-admin-sales.jpg")
    labelImgSales = ttk.Label(frameWin, image=imgSales)
    lastRow = 1
    labelImgSales.grid(column=0, row=lastRow)
    # add total sales data
    labelSales = ttk.Label(frameWin, text='Total sales:  ' + str(totalSales))
    lastRow += 1
    labelSales.grid(column=0, row=lastRow)
    # add label with units sold plot
    global imgUnits
    imgUnits = ImageTk.PhotoImage(file="img/graph-admin-units-sold.jpg")
    labelImgUnits = ttk.Label(frameWin, image=imgUnits)
    lastRow += 1
    labelImgUnits.grid(column=0, row=lastRow)
    # add label with inventory plot
    global imgInventory
    imgInventory = ImageTk.PhotoImage(file="img/graph-admin-units-sold.jpg")
    labelImgInventory = ttk.Label(frameWin, image=imgInventory)
    lastRow += 1
    labelImgInventory.grid(column=0, row=lastRow)
    # add table title for stock alerts
    tableTitle = ttk.Label(frameWin, text='Products under minimum stock')
    lastRow += 1
    tableTitle.grid(column=0, row=lastRow)
    # add the table with stock alerts, which in defined in a frame
    tableFrame = ttk.Frame(frameWin)
    lastRow += 1
    tableFrame.grid(column=0, row=lastRow)
    alertCols = ["Name", "Placement", "Minimum", "Current"]
    for tableCol in range(len(alertCols)):
        labelText = ttk.Label(tableFrame, text=alertCols[tableCol])
        labelText.grid(column=tableCol, row=0)
    for tableRow in range(len(alerts)):
        alertData = alerts[tableRow]
        for tableCol in range(len(alertData)):
            labelText = ttk.Label(tableFrame, text=alertData[tableCol])
            labelText.grid(column=tableCol, row=tableRow+1)
    return

def displaySoC(rootWin, winTitle, regCoP, initialDate, finalDate, pltImage):
    '''
    It displays in a pop-up window from the root window the data of the supplier or customer passed.
    :param rootWin:
    :param initialDate:
    :param finalDate:
    :param regCoP:
    :return:
    '''
    # set up a pop-up window and a frame inside it to place all these data
    popupWin = tkinter.Toplevel(rootWin)
    popupWin.title(winTitle)
    frameWin = createScrollableFrame(popupWin)
    # add labels with address data
    labels = ["Name: ", "Street: ", "City: ", "State: "]
    lastRow = 0
    for i in range(len(labels)):
        labelText = ttk.Label(frameWin, text=labels[i] + regCoP[i+1])
        labelText.grid(column=0, row=lastRow)
        lastRow += 1
    # add label with dates
    labelDates = ttk.Label(frameWin, text='Period from ' + initialDate + ' to ' + finalDate)
    labelDates.grid(column=0, row=lastRow)
    # add label with sales plot
    global imagePlt
    imagePlt = ImageTk.PhotoImage(file=pltImage)
    labelImgSales = ttk.Label(frameWin, image=imagePlt)
    lastRow += 1
    labelImgSales.grid(column=0, row=lastRow)
    return

def createScrollableFrame(theWindow):
    '''
    It creates a scrollable frame inside the window passed, occupying the entire window: it makes the full window
    scrollable.
    Note that Tkinter does not provide a direct way to scroll frames.
    The implementation of this function is derived from code in
    https://maxinterview.com/code/how-to-create-a-full-screen-scrollbar-in-tkinter-5161F412BBDD8D7/

    TODO: to make scroll respond the mouse wheel
    :param theWindow: the window to be scrolled
    :return: a Frame where widgets can be placed
    '''
    # create a main Frame inside the window passed
    main_frame = ttk.Frame(theWindow)
    main_frame.pack(fill="both", expand=1)
    # create a Canvas inside this  frame
    my_canvas = tkinter.Canvas(main_frame)
    my_canvas.pack(side="left", fill="both", expand=1)
    # add a Scrollbar to the Canvas
    my_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=my_canvas.yview)
    my_scrollbar.pack(side="right", fill="y")
    # configure Canvas
    my_canvas.configure(yscrollcommand=my_scrollbar.set)
    my_canvas.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
    # create another Frame INSIDE the Canvas
    second_frame = ttk.Frame(my_canvas)
    # add that new frame to a window in Canvas
    my_canvas.create_window((0, 0), window=second_frame, anchor="nw")
    return second_frame

if __name__ == '__main__':
    # create the index window to ask for admin/customer/supplier
    rootWin = tkinter.Tk()
    rootWin.title('pyCRMlite')

    def on_closing():
        '''
        It defines actions to do when it is requested to close the rootWindow
        :return: none
        '''
        if tkinter.messagebox.askokcancel("Confirm Exit", "Do you want to quit?"):
            # if answer OK, close the root window and exit script
            rootWin.destroy()
            exit()

    rootWin.protocol("WM_DELETE_WINDOW", on_closing)
    # set up the index form to ask for data
    index(rootWin)
    # start window interaction
    rootWin.mainloop()

