"""The two rollup maps, in one place.

SOC major group -> occupational family, and NAICS two-digit prefix -> industry
sector. build.py produces the aggregates from these and build_detail.py produces
the detail rows underneath them; a copy in each would let the two drift, and a
drift would show as a detail table whose rows do not add to the bar above it.
"""

SOC_MAJOR = {
 "11":"Management","13":"Business & Financial Operations","15":"Computer & Mathematical",
 "17":"Architecture & Engineering","19":"Life, Physical & Social Science",
 "21":"Community & Social Service","23":"Legal","25":"Educational Instruction & Library",
 "27":"Arts, Design, Entertainment & Media","29":"Healthcare Practitioners & Technical",
 "31":"Healthcare Support","33":"Protective Service","35":"Food Preparation & Serving",
 "37":"Building & Grounds Cleaning","39":"Personal Care & Service","41":"Sales",
 "43":"Office & Administrative Support","45":"Farming, Fishing & Forestry",
 "47":"Construction & Extraction","49":"Installation, Maintenance & Repair",
 "51":"Production","53":"Transportation & Material Moving","55":"Military",
}

NAICS_SECTOR = [
 (11,11,"Agriculture, Forestry, Fishing & Hunting"),(21,21,"Mining, Quarrying, Oil & Gas"),
 (22,22,"Utilities"),(23,23,"Construction"),(31,33,"Manufacturing"),
 (42,42,"Wholesale Trade"),(44,45,"Retail Trade"),(48,49,"Transportation & Warehousing"),
 (51,51,"Information"),(52,52,"Finance & Insurance"),(53,53,"Real Estate & Rental"),
 (54,54,"Professional, Scientific & Technical"),(55,55,"Management of Companies"),
 (56,56,"Administrative, Support & Waste Mgmt"),(61,61,"Educational Services"),
 (62,62,"Health Care & Social Assistance"),(71,71,"Arts, Entertainment & Recreation"),
 (72,72,"Accommodation & Food Services"),(81,81,"Other Services"),
 (92,92,"Public Administration"),(90,90,"Government"),
]
