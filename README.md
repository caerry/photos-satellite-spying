
**We'll commodize the space**

## Features 

- It can show all entered satellites orbits prediction in matplotlib way 
- It can use filter to show only (lowest) satellites' points, i.e with 90* elevation. The best photo quality / signal strength. 

![300](https://github.com/caerry/satellite-spying/blob/main/satellite_orbits_filtered.png?raw=true)

## Preparation 

Register on N2YO, it's free 
Locate all satellites you want to spy (NORAD ID)
Edit `config.py`

## Running 

- Ensure you've installed python 3.12+ and all the packages specified in `requirements.txt` 

- Run 

```N2YO_API_KEY=blah-blah LOT=longtitude LAT=latitude python3 main.py```

