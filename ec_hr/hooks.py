app_name = "ec_hr"
app_title = "Ecuador HR"
app_publisher = "Ecuador HR Contributors"
app_description = "Ecuadorian Human Resources and Payroll Localization (IESS, statutory benefits) for Frappe / ERPNext v16 on HRMS v16"
app_email = "developers@example.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext", "hrms"]

fixtures = []

after_install = "ec_hr.ecuador_hr.setup.after_install"
doc_events = {
	"Employee": {
		"validate": "ec_hr.ecuador_hr.employee_hooks.validate_employee",
	},
}
