def fix_lon(ds):
    '''
    adjust longitude to be [-180, 180]
    '''
    ds = ds.copy()
    
    ## TO DO FIGURE OUT HOW TO KEEP LONGITUDE ATTRIBUTES 
    if ds.lon.max()>180:
        ds.coords['lon'] = ((ds.coords['lon'] + 180) % 360 - 180) 
        ds = ds.sortby(ds.lon)

    return ds

def fix_time(ds):
    '''
    reformat time data to be a cftime.datetime object with year, month, day=1, calendar='proleptic_gregorian'
    '''
    ds = ds.copy()
    
    # get time tuples, in the form (year, month, ... )
    time_tuples = [t.timetuple() for t in ds.coords['time'].data]
    #ds.coords['time'] = [cftime.datetime(time_tuple[0], time_tuple[1], 1, calendar='proleptic_gregorian')
    #                     for time_tuple in time_tuples]
    
    ds.coords['time'] = [cftime.datetime(time_tuple[0], time_tuple[1], time_tuple[2], calendar='proleptic_gregorian')
                         for time_tuple in time_tuples]
    
    return ds


def wrapper(ds):
    '''
    clean up newly imported data
    '''
    ds = ds.copy()
    
    if ('longitude' in ds.dims) and ('latitude' in ds.dims):
        ds = ds.rename({'longitude':'lon', 'latitude': 'lat'}) # some models labelled dimensions differently...
    if ('bnds' in ds.dims): 
        ds=ds.drop_dims('bnds')
    if ('vertex' in ds.dims): 
        ds=ds.drop_dims('vertex')
    if ('height' in ds.dims): 
        ds=ds.drop_dims('height')
    if ('height' in ds): 
        ds=ds.drop_vars('height') 
    if ('depth' in ds.dims):
        ds=ds.drop_dims('depth')
    if ('depth' in ds): 
        ds=ds.drop_vars('depth') 
    
    
    # clean up the different calendars and get them all using the same cftime (hopefully)
    ds = fix_time(ds)
    # fix longitude values across all the models 
    ds = fix_lon(ds)
    return ds



### GLOBAL MEANS ###
def get_lat_name(ds):
    for lat_name in ['lat', 'latitude']:
        if lat_name in ds.coords:
            return lat_name
    raise RuntimeError("Couldn't find a latitude coordinate")

def global_mean(ds):
    """
    Calculate weighted global mean average
    """
    lat = ds[get_lat_name(ds)]
    weight = np.cos(np.deg2rad(lat))
    weight /= weight.mean()
    other_dims = set(ds.dims) - {'time'} - {'year'} - {'member_id'}
    return (ds * weight).mean(other_dims)

def region_select(ds, region_params):
    """
    subset a dataset by region
    """
    region_ds = ds.sel(lat=slice(*region_params['lat']), lon=slice(*region_params['lon']))
    return region_ds


### ANOMALIES ###

def anomalies(ds):
    '''
    Returns timeseries of anomalies (globally averaged) for a given dataset.
    '''
    try:  
        baseline = ds.sel(time = slice('1861', '1880')).groupby('time.month')
        ds_standard = (ds.groupby('time.month') - baseline.mean())/baseline.std()
        ds_anom = global_mean(ds_standard)
        return ds_anom
    except:
        print('***** error on load *****')   

### RESPONSES ###

def responses(ds):
    """
    Calculate difference between early and late period.
    Lazy.
    """

    ds = ds.copy()
    
    early_start = '1861'
    early_end = '1880'
    early = ds.sel(time=slice(early_start, early_end)).mean(dim = 'time')
    
    late_start = '2050'
    late_end = '2100'
    late = ds.sel(time = slice(late_start, late_end)).mean(dim = 'time')
    
    difference = (late - early)/early.std()
    
    return difference