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

    return (a/5*5);
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

year_hist_unique <- function (t, year, from, to, max, type="week", title="Histogram for Tickets in")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, "%b-%d")
    hbreaks<-unclass(as.POSIXct(dates))

    rows <- NULL
    for ( d in hbreaks )
    {
        d_end <- d+60*60*24
        t_sub <- t[which(t$start > d & t$start <= d_end),]
        rows <- rbind(rows, c('start'=d, 'reboots'=length(unique(t_sub$hostname))) )
    }
    rows <- data.frame(rows)

    if ( max == 0 ) {
        max = max(rows$reboots)
    }
    main<-sprintf(paste(title, "%s: MEAN %s\n"), year, mean(rows$reboots))
    print(main);
    barplot(rows$reboots, ylim=c(0,max), main=main, axes=FALSE, space=0)
    #plot(h, ylim=c(0,max), main=main, axes=FALSE)
    axis(1, labels=months, at=seq(1,length(hbreaks)))
    axis(2)
    abline(mean(rows$reboots), 0, col='grey')
    #qqnorm(h$counts)
    #qqline(h$counts)
    return (rows);
}

year_hist_unique_recent <- function (t, year, from, to, max, blocks=c(1,3,7,14,30), type="week", title="Histogram for Tickets in")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, "%b-%d")
    hbreaks<-unclass(as.POSIXct(dates))

    rows <- NULL


    for ( d in hbreaks )
    {
        # initialize row for this iteration
        row <- NULL
        row[as.character(0)] <- 0
        for ( block in blocks ) {
            row[as.character(block)] <- 0
        }

        # find the range : d plus a day
        d_end <- d+60*60*24
        # find unique hosts in this day range
        t_sub <- t[which(t$start > d & t$start <= d_end),]
        unique_hosts <- unique(t_sub$hostname)
        if (length(unique_hosts) == 0 ) { 
            rows <- rbind(rows, c('start'=d, row))
            next 
        }

        #print(sprintf("unique_hosts: %s\n", unique_hosts));
        print(sprintf("unique_hosts: %s\n", length(unique_hosts)));

        for ( host in as.character(unique_hosts) ) 
        {
            found <- 0
            for ( block in blocks )
            {
                #print(sprintf("date: %s, block: -%s, %s\n", d, block, host));
                #print(sprintf("row: %s\n", row));
                # find the range : 'block' days ago to 'd'
                d_back <- d - 60*60*24 * block
                t_back_sub <- t[which(t$start > d_back & t$start <= d),]
                u <- unique(t_back_sub$hostname)
                if ( length(u[u==host]) >= 1) 
                {
    #               add to block_count and go to next host.
                    found <- 1
                    i <- as.character(block)
                    row[i] <- row[i] + 1
                    break
                }
            }
            if ( found == 0 )
            {
                # no range found
                row['0'] <- row['0'] + 1
            }
        }
        rows <- rbind(rows, c('start'=d, row))
    }

    rows <- data.frame(rows)

    if ( max == 0 ) {
        max = max(rows['0'])
    }
    #main<-sprintf(paste(title, "%s: MEAN %s\n"), year, mean(rows$reboots))
    #print(main);
    #barplot(rows$reboots, ylim=c(0,max), main=main, axes=FALSE, space=0)
    ##plot(h, ylim=c(0,max), main=main, axes=FALSE)
    #axis(1, labels=months, at=seq(1,length(hbreaks)))
    #axis(2)
    #abline(mean(rows$reboots), 0, col='grey')
    #qqnorm(h$counts)
    #qqline(h$counts)
    return (rows);
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

abline_at_date <- function (date, col='black', lty=1, format="%Y-%m-%d")
{
    ts <-unclass(as.POSIXct(date, format=format, origin="1970-01-01"))[1]
    abline(v=ts, col=col, lty=lty)
    return (ts);
}

tstamp <- function (date, format="%Y-%m-%d")
{
    ts <- unclass(as.POSIXct(date, format=format, origin="1970-01-01"))[1]
    return (ts)
}
