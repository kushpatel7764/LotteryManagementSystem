CREATE TABLE IF NOT EXISTS TicketTimeLine (
    ScanID VARCHAR(255), 
    BookID VARCHAR(255),
    TicketNumber INTEGER,
    TicketName TEXT,
    TicketPrice INTEGER,
    created_date DATE DEFAULT CURRENT_DATE,
    created_time TIME DEFAULT CURRENT_TIME,
    updated_date DATE DEFAULT CURRENT_DATE,
    updated_time TIME DEFAULT CURRENT_TIME, 
    PRIMARY KEY(ScanID, updated_date)
);

CREATE TABLE IF NOT EXISTS Books (
    BookID VARCHAR(255) PRIMARY KEY,
    GameNumber VARCHAR(255) NOT NULL,
    Is_Sold BOOLEAN,
    BookAmount INTEGER, 
    TicketPrice INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ActivatedBooks (
    ActivationID VARCHAR(255) PRIMARY KEY,
    ActiveBookID VARCHAR(255) NOT NULL,
    isAtTicketNumber INTEGER,
    countingTicketNumber INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DailySaleReport (
    SaleDate DATE DEFAULT CURRENT_DATE PRIMARY KEY,
    InstantTicketSold INTEGER,
    OnlineTicketSold INTEGER,
    InstantTicketCashed INTEGER,
    OnlineTicketCashed INTEGER,
    CashOnHand INTEGER,
    TotalDue INTEGER
);

CREATE TABLE IF NOT EXISTS SalesLog (
    SaleDate DATE DEFAULT CURRENT_DATE,
    ActiveBookID VARCHAR(255),
    prev_TicketNum INTEGER,
    current_TicketNum INTEGER,
    Ticket_Sold_Quantity INTEGER,
    Ticket_Name TEXT,
    Ticket_GameNumber VARCHAR(255),
    PRIMARY KEY(SaleDate, ActiveBookID)
);