import os

def generate_upload_template(storms, args):
    if len(storms) != 1:
        return

    storm = storms[0]
    stormname = storm['name'].capitalize()
    season = get_season_name(storm)

    if len(storm['positions']) > 0:
        pos = storm['positions'][-1]
        print("{{WPTC track map")
        print(" | author = {{subst:REVISIONUSER}}")

        if storm['type'] == 'TD':
            print(f" | name = Tropical Depression {stormname}")
            print(f" | article = Tropical Depression {stormname} ({storm['year']})")
        elif storm['type'] == 'TS':
            print(f" | name = Tropical Storm {stormname}")
            print(f" | article = Tropical Storm {stormname} ({storm['year']})")
        elif storm['type'] == 'TY':
            print(f" | name = Typhoon {stormname}")
            print(f" | article = Typhoon {stormname} ({storm['year']})")
        elif storm['type'] == 'ST':
            print(f" | name = Super Typhoon {stormname}")
            print(f" | article = Super Typhoon {stormname} ({storm['year']})")
        elif storm['type'] == 'TC':
            print(f" | name = Tropical Cyclone {stormname}")
            print(f" | article = Tropical Cyclone {stormname} ({storm['year']})")
        elif storm['type'] == 'HU':
            print(f" | name = Hurricane {stormname}")
            print(f" | article = Hurricane {stormname} ({storm['year']})")
        elif storm['type'] == 'SD':
            print(f" | name = Subtropical Depression {stormname}")
            print(f" | article = Subtropical Depression {stormname} ({storm['year']})")
        elif storm['type'] == 'SS':
            print(f" | name = Subtropical Storm {stormname}")
            print(f" | article = Subtropical Storm {stormname} ({storm['year']})")
        else:
            print(f" | name = Cyclone {stormname}")
            print(f" | article = Cyclone {stormname} ({storm['year']})")

        print(f" | season = {season}")
        print(f" | start = {storm['year']}-{storm['month']:02d}-{storm['day']:02d}")
        print(f" | end = {pos['year']}-{pos['month']:02d}-{pos['day']:02d}")
        print(" | othersource={{{fill me}}}")
        print(" | catname={{{fill me}}}")
        print(" | code={{{fill me}}}")
        if not args.useoldcolorkey:
            print(" | colors=new")
        if args.scale == 'JMA':
            print(" | scale=JMA")
        print("}}")

        print(f"Edit summary: Refreshing information for {stormname} as of {pos['year']}-{pos['month']:02d}-{pos['day']:02d}, {pos['hour']:02d}00 UTC")

def get_season_name(storm):
    if storm['basin'] == 'AL':
        return f"{storm['year']} Atlantic hurricane season"
    elif storm['basin'] == 'EP':
        return f"{storm['year']} Pacific hurricane season"
    elif storm['basin'] == 'WP':
        return f"{storm['year']} Pacific typhoon season"
    elif storm['basin'] == 'SL':
        return "List of South Atlantic tropical cyclones"
    else:
        return "{{{fill me}}}"
