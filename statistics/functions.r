slices <- function (x, components=FALSE) 
{
    m<-x$memsize;
    d<-x$disksize/250;
    c<-x$cpuspeed;
    r<-x$numcores;
    if ( components ) {
        a<-c(m,d,c*r);
    } else {
        a<-(m+d+c*r);
    }
    return(a/2);
}

slices_2 <- function (x, components=FALSE) 
{
    # Define an ideal, then scale each measurement relative to the ideal.
    # If it matches it will be more or less than 1
    # does this scale (up or down) linearly, and why not?

    # 4, 2.4x2, 1000; 4, 3.2x1, 320; 1, 2.4x1, 160
    ideal_m <- 3.4;		# GB
    ideal_c <- 2.4;		# GHz 
    ideal_d <- 450;		# GB
    ideal_r <- 2;

    m<-x$memsize/ideal_m;
    d<-x$disksize/ideal_d;
    c<-x$cpuspeed/ideal_c;
    r<-x$numcores/ideal_r;
    # ideal is 1

    if ( components ) {
        a<-c(m,d,c*r);
    } else {
        a<-(m+d+c*r);
    }

    return (a/3*5);
}

slices_3 <- function (x, components=FALSE) 
{
    # Define an ideal, then scale each measurement relative to the ideal.
    # If it matches it will be more or less than 1
    # does this scale (up or down) linearly, and why not?

    # 4, 2.4x2, 1000; 4, 3.2x1, 320; 1, 2.4x1, 160
    ideal_m <- 3.4; #GB
    ideal_c <- 2.4; #GHz
    ideal_d <- 450;	#GB
    ideal_r <- 2;
	ideal_bw <- 100000;	 #Kbps

    m<-x$memsize/ideal_m;
    d<-x$disksize/ideal_d;
    c<-x$cpuspeed/ideal_c;
    r<-x$numcores/ideal_r;
    b<-log(x$bwlimit)/log(ideal_bw);
    # ideal is 1

    if ( components ) {
        a<-c(m,d,c*r,b);
    } else {
        a<-(m+d+c*r+b);
    }

    return (a/4*5);
}

slices_4 <- function (x, components=FALSE) 
{
    # Define an ideal, then scale each measurement relative to the ideal.
    # If it matches it will be more or less than 1
    # does this scale (up or down) linearly, and why not?

    # 4, 2.4x2, 1000; 4, 3.2x1, 320; 1, 2.4x1, 160
    ideal_m <- 3.4; #GB
    ideal_c <- 2.4; #GHz
    ideal_d <- 450;	#GB
    ideal_r <- 2;
	ideal_bw <- 100000;	 #Kbps
	ideal_pcu <- 1;

    m<-x$memsize/ideal_m;
    d<-x$disksize/ideal_d;
    c<-x$cpuspeed/ideal_c;
    r<-x$numcores/ideal_r;
    b<-log(x$bwlimit)/log(ideal_bw);
	p<-x$pcustatus/ideal_pcu;
    # ideal is 1

    if ( components ) {
        a<-c(m,d,c*r,b,p);
    } else {
        a<-(m+d+c*r+b+p);
    }

    return (a/5*5);     # I know. Preserved for clarity and consistency with earlier examples
}

index_of_bin <- function (h, value)
{
    index <- 0;

    for (i in sequence(length(h$breaks))) 
    {
        # first bin

        if ( value < h$breaks[1] )
        {
            index <- 1;
            break;
        } 

        # last bin

        if ( i == length(h$breaks) )
        {
            # end of line
            index <- i;
            break;
        } 

        # all other bins

        if ( value > h$breaks[i] && value <= h$breaks[i+1] )
        {
            index <- i+1;
            break;
        } 
    }
    if ( index == 0 ) {
        warning("index == 0, no bin assigned for value: ", value);
    }

    return (index);
}

start_image <- function (name, width=480, height=480)
{
    png(name, width=width, height=height);
}

end_image <- function ()
{
    dev.off()
}


plot_rt_hist <- function (t, imagename=0)
{
    d2 <- (t$lastreply - t$start)
    std_dev <- sd(log(d2))
    m <- mean(log(d2))
    print(sprintf("mean: %s, stddev: %s\n", m, std_dev));

    if ( imagename != 0 ) { start_image(imagename) }

    h<-hist(log(d2), 
        xlab="Hours between ticket creation and final reply", 
        main="Time to Final Reply for RT Tickets", axes=FALSE)
    
    a<-exp(h$breaks)/(60*60)    # convert units from log(secs) to hours
    axis(1,labels=signif(a,2), at=h$breaks)
    axis(2)

    x<-seq(min(h$breaks),max(h$breaks),length=500)
    y<-dnorm(x,mean=m, sd=std_dev)

    # scale y to the size of h's 'counts' vector rather than the density function
    lines(x,y*max(h$counts)/max(y))
    if ( imagename != 0 ) { end_image() }
}

year_hist <- function (t, year, from, to, max, type="week", title="Histogram for Tickets in", fmt="%b-%d")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, fmt)
    hbreaks<-unclass(as.POSIXct(dates))
    h<-hist(t$start, breaks=hbreaks, plot=FALSE)
    main<-sprintf(paste(title, "%s: MEAN %s\n"), year, mean(h$counts))
    print(main);
    print(h$counts);
    if ( max == 0 ) {
        max = max(h$counts)
    }
    plot(h, ylim=c(0,max), main=main, axes=FALSE)
    axis(1, labels=months, at=hbreaks)
    axis(2)
    abline(mean(h$counts), 0, col='grey')
    #qqnorm(h$counts)
    #qqline(h$counts)
    return (h);
}


source("myImagePlot.R")
reboot_image <- function (t, year, from, to, max=0, type="week", title="")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, "%b-%d")
    hbreaks<-unclass(as.POSIXct(dates))

    rows <- NULL
    image <- matrix(data=0, nrow=max(as.numeric(t$hostname)), ncol=length(hbreaks))
    #image <- matrix(data=0, nrow=length(unique(t$hostname)), ncol=length(hbreaks))

    #for ( d in hbreaks )
    for ( i in seq(1, length(hbreaks)) )
    {
        # find the range : d plus a day
        d <- hbreaks[i]
        d_end <- d+60*60*24
        # find unique hosts in this day range
        t_sub <- t[which(t$start > d & t$start <= d_end),]
        unique_hosts <- unique(t_sub$hostname)
        if (length(unique_hosts) == 0 ) { next }

        for ( host in unique_hosts ) 
        {
            image[host,i] <- 1
        }
    }

    myImagePlot(image, xLabels=months, yLabels=c(""), title=title)

            #found <- 0
            #for ( block in blocks )
            #{
                #print(sprintf("date: %s, block: -%s, %s\n", d, block, host));
                #print(sprintf("row: %s\n", row));
                # find the range : 'block' days ago to 'd'
            #    d_back <- d - 60*60*24 * block
            #    t_back_sub <- t[which(t$start > d_back & t$start <= d),]
            #    u <- unique(t_back_sub$hostname)
            #    if ( length(u[u==host]) >= 1) 
            #    {
    #       #        add to block_count and go to next host.
            #        found <- 1
            #        i <- as.character(block)
            #        row[i] <- row[i] + 1
            #        break
            #    }
            #}
            #if ( found == 0 )
            #{
            #    # no range found
            #    row['0'] <- row['0'] + 1
            #}
        #}
        #rows <- rbind(rows, c('start'=d, row))

    #rows <- data.frame(rows)

    #if ( max == 0 ) {
    #    max = max(rows['0'])
    #}
    #main<-sprintf(paste(title, "%s: MEAN %s\n"), year, mean(rows$reboots))
    #print(main);
    #barplot(rows$reboots, ylim=c(0,max), main=main, axes=FALSE, space=0)
    ##plot(h, ylim=c(0,max), main=main, axes=FALSE)
    #axis(1, labels=months, at=seq(1,length(hbreaks)))
    #axis(2)
    #abline(mean(rows$reboots), 0, col='grey')
    #qqnorm(h$counts)
    #qqline(h$counts)
    return (image);
}

add_year <- function (t)
{
    t$year <- c(0)  # assign new column with zero value initially
    for ( i in 1:length(t$start) )
    {
        d <- as.POSIXlt(t$start[i], origin="1970-01-01")
        year <- d$year + 1900 # as.numeric(format(d, "%Y"))
        t$year[i] <- year
    }
    return (t);
}

add_timestamp <- function (t)
{
    t$start <- c(0)  # assign new column with zero value initially
    for ( i in 1:length(t$date) )
    {
        tstamp <-unclass(as.POSIXct(t$date[i], origin="1970-01-01"))[1]
        t$start[i] <- tstamp
    }
    return (t);
}

convert_datestr <- function (t, format)
{
    t$start <- c(0)  # assign new column with zero value initially
    for ( i in 1:length(t$Date) )
    {
        tstamp <-unclass(as.POSIXct(strptime(t$Date[i], format)))[1]
        t$start[i] <- tstamp
    }
    return (t);
}

abline_at_date <- function (date, col='black', lty=1, format="%Y-%m-%d", height=0)
{
    ts <-unclass(as.POSIXct(date, format=format, origin="1970-01-01"))[1]
    if ( height == 0 )
    {
        abline(v=ts, col=col, lty=lty)
    } else {
        lines(c(ts,ts),c(0,height), col=col, lty=lty)
    }
    return (ts);
}

tstamp <- function (date, format="%Y-%m-%d")
{
    ts <- unclass(as.POSIXct(date, format=format, origin="1970-01-01"))[1]
    return (ts)
}

lowess_smooth <- function (x, y, delta=(60*60*24), f=0.02)
{
    a<-lowess(x, y, delta=delta, f=f)
    return (a);
}

in_list <- function ( str, str_list )
{
    for ( f in str_list )
    {
        if ( str == f )
        {
            return (TRUE);
        }
    }
    return (FALSE);
}

col2hex <- function  (colorname, alpha=1)
{
    hex = "FFFFFFFF";
    c_rgb <- col2rgb(colorname)
    c_rgb <- c_rgb / 255
    hex <- rgb(c_rgb[1,1], c_rgb[2,1], c_rgb[3,1], alpha)
    return (hex);
}

printf <- function (...)
{
    return(print(sprintf(...)));
}

time_graph_setup <- function (from, to)
{
    # find 'type' range of days
    xlim <- c(tstamp(from, format="%Y/%m/%d"), tstamp(to, format="%Y/%m/%d"))

    begin_date <- as.Date(from)
    end_date <- as.Date(to)

    begin_day <- as.numeric(format(begin_date, "%j"))
    end_day <- as.numeric(format(end_date, "%j"))
    print(begin_day)

    date_days <-seq(as.Date(from), as.Date(to), 'day')
    date_weeks <-seq(as.Date(from), as.Date(to), 'week')
    date_months <-seq(as.Date(from), as.Date(to), 'month')
    date_years <-seq(as.Date(from), as.Date(to), 'year')

    day_str <- format(date_months, "%a")
    day_ts <- unclass(as.POSIXct(date_days))

    week_str <- format(date_months, "%W")
    week_ts <- unclass(as.POSIXct(date_weeks))

    month_str <- format(date_months, "%b")
    month_ts <- unclass(as.POSIXct(date_months))

    year_str <- format(date_years, "%Y")
    year_ts <- unclass(as.POSIXct(date_years))
    print(year_ts)
    year_ts_before <- year_ts

    l <- length(year_ts)
    print(l)
    if ( l == 1 ) {
        # center year between begin_day and end_day
        print("one year!")
        year_ts[1] <- (xlim[1] + xlim[2]) / 2.0
    } else 
    {
        print("multitple years!")
        # center first year between start day and last day of that year.
        print(year_ts)
        year_ts[1] <- year_ts[1] + ((365 - begin_day)/2.0)*60*60*24
        print(year_ts)
        year_ts[l] <- year_ts[l] + ( -begin_day + end_day/2.0)*60*60*24
        print(year_ts)
        if ( l > 2 ) {
            year_ts <- c(year_ts[1], year_ts[seq(2,l-1)] + (180 - begin_day)*60*60*24, year_ts[l])
        }
        print(year_ts)
    }
    print(year_ts - year_ts_before)
        
    return (list(xlim=xlim, day_str=day_str, day_ts=day_ts,
                 week_str=week_str, week_ts=week_ts, 
                 month_str=month_str, month_ts=month_ts, 
                 year_str=year_str, year_ts=year_ts))
}

planetlab_releases <- function (height) 
{
    h = height
    tstamp_20040412 <-abline_at_date("2004-04-12", col='white', lty=0, height=h)
    tstamp_20041112 <-abline_at_date("2004-11-12", col='white', lty=3, height=h)
    tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=3, height=h)
    tstamp_20050615 <-abline_at_date("2005-06-15", col='white',  lty=0, height=h)
    tstamp_20051001 <-abline_at_date("2005-10-01", col='grey60', lty=3, height=h)
    tstamp_20060519 <-abline_at_date("2006-05-19", col='grey60', lty=3, height=h)
    tstamp_20070228 <-abline_at_date("2007-02-28", col='grey60', lty=3, height=h)
    tstamp_20070501 <-abline_at_date("2007-05-01", col='white',  lty=0, height=h)
    tstamp_20071021 <-abline_at_date("2007-10-21", col='grey60', lty=3, height=h)
    tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=3, height=h)
    tstamp_20080815 <-abline_at_date("2008-08-15", col='white',  lty=0, height=h)
    tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=3, height=h)
    tstamp_20100201 <-abline_at_date("2010-02-01", col='white',  lty=0, height=h)
    tstamp_20100628 <-abline_at_date("2010-06-28", col='white', lty=3, height=h)
    tstamp_20110222 <-abline_at_date("2011-02-22", col='grey60', lty=3, height=h)
    # I think 5.0 was released 02/22/2011... not 03-09

    text(x=c(tstamp_20040412,
            tstamp_20041112,
            tstamp_20050301,
            tstamp_20050615,
            tstamp_20051001,
            tstamp_20060519,
            tstamp_20070228,
            tstamp_20071021,
            tstamp_20080601,
            tstamp_20090501,
            tstamp_20100628,
            tstamp_20110222),
         y=c(h-h*0.05),
         #labels=c('Release', '3.0', '3.1', '', '3.2', '3.3', '4.0', '4.1', '4.2', '4.3')) 
         labels=c('', '', '3.1', '', '3.2', '3.3', '4.0', '4.1', '4.2', '4.3', '', '5.0')) 
    text(x=c(tstamp_20050301), y=c(h), labels=c("Releases"))
}

plc_releases <- function (height) 
{
    h = height
    tstamp_pre <-abline_at_date("2004-10-01", col='grey60', lty=3, height=h)
    tstamp_3_1 <-abline_at_date("2005-03-01", col='grey60', lty=3, height=h)
    tstamp_3_2 <-abline_at_date("2005-10-01", col='grey60', lty=3, height=h)
    tstamp_3_3 <-abline_at_date("2006-05-19", col='grey60', lty=3, height=h)
    tstamp_4_0 <-abline_at_date("2007-02-28", col='grey60', lty=3, height=h)
    tstamp_4_1 <-abline_at_date("2007-10-21", col='grey60', lty=3, height=h)
    tstamp_4_2 <-abline_at_date("2008-06-01", col='grey60', lty=3, height=h)
    tstamp_4_3 <-abline_at_date("2009-05-01", col='grey60', lty=3, height=h)
    tstamp_5_0 <-abline_at_date("2011-02-22", col='grey60', lty=3, height=h)

    text(x=c(tstamp_3_1,
            tstamp_3_2,
            tstamp_3_3,
            tstamp_4_0,
            tstamp_4_1,
            tstamp_4_2,
            tstamp_4_3,
            tstamp_5_0),
         y=c(h-h*0.05),
         labels=c('3.1', '3.2', '3.3', '4.0', '4.1', '4.2', '4.3', '5.0')) 
    text(x=c(tstamp_pre), y=c(h), labels=c("Releases"))
}
