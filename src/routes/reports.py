from flask import Blueprint, render_template, request, jsonify, url_for, redirect
from database import DatabaseQueries
from utils.config import db_path, load_config
from utils.error_hanlder import check_error
from datetime import datetime
from utils.reports import calculate_instant_tickets_sold, create_daily_invoice
from utc_to_local_time import convert_utc_to_local
from database import Database, DatabaseQueries
from utils.tickets import insert_ticket

report_bp = Blueprint('reports', __name__)

@report_bp.route('/edit_reports', methods=["GET", "POST"])
def edit_reports():
    # Safely load all reports
    msg_data = {"message": "", "message_type": ""}
    sales_reports = check_error(DatabaseQueries.get_all_sales_reports(db_path), msg_data, fallback=[])
    
    # Convert to local date and time and filter
    local_reports = []
    filter_date = request.args.get("date")
    
    filter_time = None
    filter_time_military = request.args.get("time")
    if filter_time_military:
        try:
            filter_time_obj = datetime.strptime(filter_time_military, "%H:%M")
            # Format to regular time with AM/PM
            filter_time = filter_time_obj.strftime("%I:%M %p")
        except ValueError:
            msg_data["message"] = "Invalid time format. Please use HH:MM (24-hour format)."
            msg_data["message_type"] = "error"
            filter_time = None  # Fail gracefully
    
    # convert sales report date and time from utc to local
    for report in sales_reports:
        try:
            utc_date = datetime.strptime(report["ReportDate"], "%Y-%m-%d").date()
            utc_time = datetime.strptime(report["ReportTime"], "%H:%M:%S").time()
            local_date = convert_utc_to_local(utc_date, 'America/New_York').strftime("%Y-%m-%d")
            local_time = convert_utc_to_local(utc_time, 'America/New_York').strftime("%I:%M %p")
            # Filter logic
            match = True
            if filter_date:
                if local_date != filter_date:
                    match = False
            if filter_time:
                if not local_time.startswith(filter_time):
                    match = False

            if match:
                report["ReportDate"] = local_date
                report["ReportTime"] = local_time
                local_reports.append(report)
        except Exception as e:
            msg_data["message"] = f"Skipping report due to error: {e}"
            msg_data["message_type"] = "error"
            continue
    return render_template("edit_reports.html", sales_reports=local_reports, message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))

@report_bp.route("/edit_report/<report_id>/<updated_report_ids>",  methods=["GET", "POST"])
def edit_single_report(report_id, updated_report_ids=None):
    message = request.args.get("message", "")
    message_type = request.args.get("message_type", "")
    
    msg_data = {"message": message, "message_type": message_type}
    # Query the sales logs related to this report ID
    sales_logs = check_error(DatabaseQueries.get_sales_log(db_path, report_id), message_holder=msg_data, fallback=[])
    sale_report = check_error(DatabaseQueries.get_daily_report(db_path, report_id), message_holder=msg_data, fallback={})
    # Instant ticket sold recalculation
    if sale_report:
        instant_tickets_sold_total = check_error(calculate_instant_tickets_sold(ReportID=report_id), msg_data, fallback=0)
        sale_report["InstantTicketSold"] = instant_tickets_sold_total
    # Get the counting order to calc sold
    counting_order = load_config()['ticket_order']
    return render_template("edit_single_report.html", 
                           report_id=report_id, 
                           sales_logs=sales_logs, 
                           sale_report=sale_report, 
                           counting_order=counting_order, 
                           updated_report_ids=updated_report_ids,
                           message=message,
                           message_type=message_type) 
    
@report_bp.route("/update_salesLog", methods=["GET", "POST"])
def update_sales_log():
    msg_data = {"message": "", "message_type": ""}
    updated_report_ids = []
    try:
        data = request.get_json()
        book_id = data.get('bookID')
        report_id = data.get("reportID") # str type
        open = data.get("open")
        close = data.get("close")
        
        report_id_int = int(report_id)
        previous_reportID = report_id_int - 1
        next_reportID = report_id_int + 1
        latest_reportID = int(check_error(lambda: DatabaseQueries.next_report_ID(db_path), msg_data)) - 1
        
        game_number = check_error(DatabaseQueries.get_game_num_of(db_path, book_id), msg_data)
        is_book_sold = check_error(DatabaseQueries.is_sold(db_path, book_id), msg_data)
        
        book = check_error(DatabaseQueries.get_book(db_path, book_id), msg_data)
        TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), msg_data)
        book_amount = book[3]
        TicketPrice = book[4]
        scanID = f"{game_number}{book_id}{close}{TicketPrice}{book_amount}" 
        
        
        # Main update for current report
        check_error(Database.update_sales_log_prev_TicketNum(db_path, open, report_id, book_id), msg_data) 
        check_error(Database.update_sales_log_current_TicketNum(db_path, close, report_id, book_id), msg_data)
        updated_report_ids.append(report_id_int)

        # Book is sold and user now closes it (removing sold status)
        if is_book_sold and close != "-1":
            # Update Is_Sold attribute to not sold for this book id.
            check_error(Database.update_is_sold_for_book(db_path, False, book_id), msg_data)
            # Update salesLog and TicketTimeline
            for id in range(report_id_int + 1, latest_reportID + 1):
                TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), msg_data)
                # Add salesLog
                sale_log_info = {
                "ReportID": str(id), 
                "ActiveBookID": book_id,
                "prev_TicketNum": close, # index 4 is the isAtTicketNumber
                "current_TicketNum": close,
                "Ticket_Name": TicketName,
                "Ticket_GameNumber": game_number
                }
                check_error(Database.insert_sales_log(db_path, sale_log_info), msg_data)
                # A update in sale log means the instant sold should also be updated
                instant_sold = check_error(calculate_instant_tickets_sold(id), msg_data)
                check_error(Database.update_sale_report_instant_sold(db_path, instant_sold, id), msg_data)
                # Insert ticket for the book sold out
                check_error(insert_ticket(scanID, book_id, close, TicketName, TicketPrice, str(id)), msg_data)
            
            # Re-activate book with correct ticket position
            activate_book_info = {
                "ActivationID": scanID,
                "ActiveBookID": book_id,
                "isAtTicketNumber": close
            }
            check_error(Database.insert_book_to_ActivatedBook_table(database_path=db_path, active_book_info=activate_book_info), msg_data)

        # Update previous report if it exists
        if (not previous_reportID < 1):
            check_error(Database.update_ticketTimeline_ticketnumber(db_path, previous_reportID, book_id, open), msg_data)
            check_error(Database.update_sales_log_current_TicketNum(db_path, open, previous_reportID, book_id), msg_data)
            prev_instant_sold = check_error(calculate_instant_tickets_sold(previous_reportID), msg_data)
            check_error(Database.update_sale_report_instant_sold(db_path, prev_instant_sold, previous_reportID), msg_data)
            updated_report_ids.append(previous_reportID)
            
        # Update next report if it exists
        if (next_reportID <= latest_reportID):
            check_error(Database.update_sales_log_prev_TicketNum(db_path, close, next_reportID, book_id), msg_data)
            next_instant_sold = check_error(calculate_instant_tickets_sold(next_reportID), msg_data)
            check_error(Database.update_sale_report_instant_sold(db_path, next_instant_sold, next_reportID), msg_data)
            updated_report_ids.append(next_reportID)

        # If current is the latest report, update isAtTicketNumber
        if (latest_reportID == report_id_int):
            check_error(Database.update_isAtTicketNumber_val(db_path, book_id, close), msg_data)
        # Update ticket timeline and instant sold for current
        # A update in sale log means the instant sold should also be updated
        instant_sold = check_error(calculate_instant_tickets_sold(report_id), msg_data)
        check_error(Database.update_sale_report_instant_sold(db_path, instant_sold, report_id), msg_data)
        check_error(Database.update_ticketTimeline_ticketnumber(db_path, report_id, book_id, close), msg_data)
        
        return jsonify({"redirect_url": url_for("reports.edit_single_report", report_id=report_id, updated_report_ids=updated_report_ids.__str__(),  message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))})
    except Exception as e: 
        msg_data["message"] = str(e)
        msg_data["message_type"] = "error"
        safe_report_id = report_id if 'report_id' in locals() else "unknown"
        return jsonify({"redirect_url": url_for("reports.edit_single_report", report_id=safe_report_id, updated_report_ids=updated_report_ids.__str__(), message=str(e), message_type="error")})
    

@report_bp.route("/update_sale_report/<report_id>", methods=["GET","POST"])
def update_sale_report(report_id):
    msg_data = {"message": "", "message_type": ""}
    try:
        if request.method == "POST":
            instant_sold = request.form["instant_sold"]
            online_sold = request.form["online_sold"]
            instant_cashed = request.form["instant_cashed"]
            online_cashed = request.form["online_cashed"]
            cash_on_hand = request.form["cash_on_hand"]
            
            check_error(Database.update_sale_report(db_path, instant_sold, online_sold, instant_cashed, online_cashed, cash_on_hand, report_id), message_holder=msg_data)
        return redirect(url_for("reports.edit_single_report", report_id=report_id, updated_report_ids="None"), message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))
    except ValueError as e:
        return redirect(url_for("reports.edit_single_report", report_id=report_id, updated_report_ids="None", message=str(e), message_type="error"))
 

@report_bp.route('/download/<int:report_id>', methods=['GET']) # change to GET for easier triggering
def download_modified_report(report_id): 
    msg_data = {"message": "", "message_type": ""}
    result = check_error(lambda: create_daily_invoice(report_id), msg_data)
    
    if msg_data.get("message_type") == "error":
        return msg_data["message"], msg_data["message_type"]
    
    return result

