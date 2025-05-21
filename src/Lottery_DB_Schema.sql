CREATE TABLE IF NOT EXISTS TicketScan (
    ScanID VARCHAR(255) PRIMARY KEY, 
    BookID INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    TicketNumber INTEGER
    
);

CREATE TABLE IF NOT EXISTS Books (
    BookID INTEGER PRIMARY KEY,
    GameNumber INTEGER NOT NULL,
    BookAmount INTEGER,
    isAtTicketNumber INTEGER, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ActivatedBooks (
    ActivationID VARCHAR(255) PRIMARY KEY,
    ActiveBookID INTEGER NOT NULL,
    Is_Sold BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS TicketTimeline (
    TicketNumber INTEGER,
    BookID INTEGER,
    TicketName TEXT,
    TicketPrice INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    PRIMARY KEY (TicketNumber, BookID, updated_at)
);

CREATE TABLE IF NOT EXISTS DailySaleReport (
    SaleDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,
    InstantTicketSold INTEGER,
    OnlineTicketSold INTEGER,
    InstantTicketCashed INTEGER,
    OnlineTicketCashed INTEGER,
    CashDue INTEGER,
    TotalDue INTEGER
);

CREATE TABLE IF NOT EXISTS SalesLog (
    SaleDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ActiveBookID INTEGER,
    prev_TicketNum INTEGER,
    current_TicketNum INTEGER,
    Ticket_Sold_Quantity INTEGER,
    Ticket_Name TEXT,
    Ticket_GameNumber INTEGER
    PRIMARY KEY(SaleDate, ActiveBookID)
);