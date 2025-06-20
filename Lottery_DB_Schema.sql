CREATE TABLE IF NOT EXISTS TicketTimeLine (
    ScanID Text, 
    ReportID Text NOT NULL DEFAULT "Pending",
    BookID Text NOT NULL,
    TicketNumber INTEGER NOT NULL,
    TicketName TEXT,
    TicketPrice INTEGER NOT NULL,
    created_date DATE DEFAULT CURRENT_DATE,
    created_time TIME DEFAULT CURRENT_TIME,
    updated_date DATE DEFAULT CURRENT_DATE,
    updated_time TIME DEFAULT CURRENT_TIME, 
    PRIMARY KEY(BookID, ReportID),
    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE
    FOREIGN KEY (ReportID) REFERENCES SalesLog(ReportID) ON DELETE CASCADE
);

-- All books (unactivated/activated/sold)
CREATE TABLE IF NOT EXISTS Books (
    BookID Text PRIMARY KEY,
    GameNumber Text NOT NULL,
    Is_Sold BOOLEAN NOT NULL DEFAULT 0,
    BookAmount INTEGER NOT NULL, 
    TicketPrice INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (GameNumber) REFERENCES TicketNameLookup(GameNumber)
);

CREATE TABLE IF NOT EXISTS ActivatedBooks (
    ActivationID Text PRIMARY KEY,
    ActiveBookID Text NOT NULL,
    isAtTicketNumber INTEGER,
    countingTicketNumber INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ActiveBookID) REFERENCES Books(BookID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS SaleReport (
    ReportID Text PRIMARY KEY, 
    ReportDate DATE DEFAULT CURRENT_DATE,
    ReportTime TIME DEFAULT CURRENT_TIME, 
    InstantTicketSold INTEGER NOT NULL DEFAULT 0,
    OnlineTicketSold INTEGER NOT NULL DEFAULT 0,
    InstantTicketCashed INTEGER NOT NULL DEFAULT 0,
    OnlineTicketCashed INTEGER NOT NULL DEFAULT 0,
    CashOnHand INTEGER NOT NULL DEFAULT 0,
    TotalDue INTEGER GENERATED ALWAYS AS ((InstantTicketSold + OnlineTicketSold) - (InstantTicketCashed + OnlineTicketCashed)) STORED, 
    FOREIGN KEY (ReportID) REFERENCES SaleLog(ReportID)
);

CREATE TABLE IF NOT EXISTS SalesLog (
    ReportID Text NOT NULL DEFAULT "Pending", -- Session in day
    LogDate DATE DEFAULT CURRENT_DATE, -- Day
    LogTime TIME DEFAULT CURRENT_TIME,
    ActiveBookID Text NOT NULL, -- Book
    prev_TicketNum INTEGER NOT NULL,
    current_TicketNum INTEGER NOT NULL,
    Ticket_Sold_Quantity INTEGER NOT NULL,
    Ticket_Name TEXT,
    Ticket_GameNumber TEXT,
    PRIMARY KEY (ReportID, ActiveBookID)
);

-- Lookup table for ticket names
CREATE TABLE IF NOT EXISTS TicketNameLookup (
    GameNumber Text PRIMARY KEY,
    TicketName Text NOT NULL DEFAULT "N/A" 
);