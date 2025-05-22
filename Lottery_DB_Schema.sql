CREATE TABLE IF NOT EXISTS TicketScan (
    ScanID VARCHAR(255) PRIMARY KEY, 
    BookID VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    TicketNumber INTEGER
);

CREATE TABLE IF NOT EXISTS Books (
    BookID VARCHAR(255) PRIMARY KEY,
    GameNumber VARCHAR(255) NOT NULL,
    BookAmount INTEGER,
    isAtTicketNumber INTEGER, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ActivatedBooks (
    ActivationID VARCHAR(255) PRIMARY KEY,
    ActiveBookID VARCHAR(255) NOT NULL,
    Is_Sold BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS TicketTimeline (
    TicketNumber INTEGER,
    BookID VARCHAR(255),
    TicketName TEXT,
    TicketPrice INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (TicketNumber, BookID, updated_at)
);

CREATE TABLE IF NOT EXISTS DailySaleReport (
    SaleDate DATE DEFAULT CURRENT_DATE PRIMARY KEY,
    InstantTicketSold INTEGER,
    OnlineTicketSold INTEGER,
    InstantTicketCashed INTEGER,
    OnlineTicketCashed INTEGER,
    CashDue INTEGER,
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