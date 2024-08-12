
def format_date(date : str):
    operating_str = ""
    hr = ""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i,h in enumerate(date.lower().split(",")):
        if operating_str == "" and h.strip() not in ["closed", "unknown", "n,/,a"]:
            hr = h
            operating_str += days[i]

        if h.strip() != hr.strip() and h.strip() not in ["closed", "unknown", "n,/,a"]:
            if hr.strip() != "":
                operating_str += " - " + days[i] + " Open -> " + hr

            hr = h
            operating_str += "\n" + days[i]

        if h.strip() in ["closed", "unknown", "n,/,a"]:
            if hr == "":
                continue

            operating_str += " - " + days[i - 1] + " Open -> " + hr
            hr = ""

        if i == 6 and h.strip() not in ["closed", "unknown", "n,/,a"]:
            operating_str += " - " + days[i] + " Open -> " + hr

    if hr!= "":
        return "UNKNOWN"
    return operating_str