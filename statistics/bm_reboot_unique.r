
source("functions.r");

# system("parse_rt_data.py > rt_data.csv");
# ./bmevents.py events.1-18-10 BootUpdateNode > bm_reboot_2010-01-18.csv
# ./bmevents.py events.10-08-09 BootUpdateNode > bm_reboot_2009-10-08.csv 
# ./bmevents.py events.29.12.08.dump BootUpdateNode > bm_reboot_2008-12-29.csv
# ./bmevents.py events.8-25-09.dump BootUpdateNode > bm_reboot_2009-08-25.csv
# 
bm <- read.csv('bm_reboot.csv', sep=',', header=TRUE)
bm_api <- read.csv('bm_reboot_2008-12-29.csv', sep=',', header=TRUE)

bm2<-bm

tstamp_78 <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))[1]
tstamp_89 <-unclass(as.POSIXct("2009-01-01", origin="1960-01-01"))[1]

bm_7 <- bm2[which( bm2$start < tstamp_78 ),]
bm_8 <- bm2[which( bm2$start >= tstamp_78 & bm2$start < tstamp_89 ),]
bm_9 <- bm2[which( bm2$start >= tstamp_89 ),]

tstamp <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))
bm_67 <- bm2[which( bm2$start <  tstamp[1] ),]
bm_89 <- bm2[which( bm2$start >= tstamp[1] ),]


#start_image("bm_reboot.png")

par(mfrow=c(2,1))
par(mai=c(.5,.4,.5,.4))
#year_hist(bm_9, "2009", "2009/06/21", "2010/2/10", 500, 'day', "Daily Reboot Rates")
#rows <- year_hist_unique(bm_9, "2009", "2009/06/21", "2010/2/10", 100, 'day', "Unique Daily Reboots")
#end_image()

if ( TRUE )
{
    rows_blocks <- year_hist_unique_recent(bm_9, "2009", "2009/06/21", "2010/2/10", 100, c(1,3,7,14,30), 'day', "Unique Daily Reboots")

    x<-NULL
    blocks <- c(0,1,3,7,14,30)
    for ( b in blocks ) { x<- c(x, paste("X", b, sep="")) }

    par(mfrow=c(1,1))
    par(mai=c(1,.7,.5,.4))
    start_image("bm_reboot_color.png", width=900)

    barplot(t(rows_blocks[x]), border=NA, col=c('purple', 'blue', 'green', 'red', 'pink', 'orange', 'yellow'), ylim=c(0,100), main="How Recently Node were Rebooted", xlab="Days from June-2009 to Jan-2010", space=0, legend=c("Only today", "Also within 1 day", "Also within 3 days", "Also within 7 days", "Also within 14 days", "Also within 30 days"), ylab="Frequency")
    end_image()

    #barplot(rows_blocks$X0, border=NA, col=c('purple', 'blue', 'green', 'red', 'pink', 'orange', 'yellow'), ylim=c(0,100))

    #par(mfrow=c(6,1))
    #par(mai=c(.1,.7,.1,.1))
    #barplot(rows_blocks$X0, border=NA, col=c('purple'), ylim=c(0,100))
    #barplot(rows_blocks$X1, border=NA, col=c('blue'), ylim=c(0,100))
    #barplot(rows_blocks$X3, border=NA, col=c('green'), ylim=c(0,100))
    #barplot(rows_blocks$X7, border=NA, col=c('red'), ylim=c(0,100))
    #barplot(rows_blocks$X14, border=NA, col=c('pink'), ylim=c(0,100))
    #barplot(rows_blocks$X30, border=NA, col=c('orange'), ylim=c(0,100))

    shapiro.test(rows_blocks$X0[ rows_blocks$X0 < 50 ])
    shapiro.test(rows_blocks$X1[ rows_blocks$X1 < 50 ])
    shapiro.test(rows_blocks$X3[ rows_blocks$X3 < 50 ])
    shapiro.test(rows_blocks$X7[ rows_blocks$X7 < 50 ])
    shapiro.test(rows_blocks$X14[ rows_blocks$X14 < 50 ])
    shapiro.test(rows_blocks$X30[ rows_blocks$X30 < 50 ])
}


#image <- reboot_image(t_9, "2009", "2009/06/21", "2010/2/10", 0, 'day')
#myImagePlot(image)

start_image("st_bm_reboots.png", width=400, height=600)
image <- reboot_image(bm_9, "2009", "2009/06/21", "2010/2/10", 0, 'day', title="BootManager Reboots for all Nodes")
end_image()

start_image("st_api_event_reboots.png", width=800, height=600)
image2 <- reboot_image(bm_api, "2009", "2008/06/21", "2010/2/10", 0, 'day', title= "API Reboot Events for all Nodes")
end_image()

reboot_frequency <- function ( img )
{
    d <- dim(img)
    # for each row
    f <- NULL
    for ( i in seq(1:d[1]) )
    {
        r <- img[i,]
        f <- c(f, sum(r))
    }
    return (f);
}

reboot_events <- function ( img )
{
    d <- dim(img)
    # for each row
    f <- NULL
    for ( i in seq(1:d[2]) )
    {
        c <- img[,i]
        f <- c(f, sum(c))
    }
    return (f);
}

time_to_reboot <- function (img, first=0, last=0)
{
    d <- dim(img)
    # for each row
    f <- NULL
    for ( i in seq(1:d[1]) )
    {
        if (last == 0 ) { last <- length(img[i,]) }
        r <- img[i,first:last]
        # find  first reboot
        start_i <- 1
        while ( start_i < length(r) && r[start_i] != 1 ) 
        { 
            start_i <- start_i + 1 
        }
        end_i <- start_i

        while ( start_i < length(r) )
        {
            if ( r[start_i] == 1 && start_i != end_i)
            {
                f <- c(f, start_i-end_i)
                while ( start_i < length(r) && r[start_i] == 1 ) { start_i <- start_i + 1 }
                end_i <- start_i
            }
            start_i <- start_i + 1
        }
    }
    return (f);
}

find_95 <- function (cdf, low=0, high=1000) 
{
    # find the lowest point past the 95th percentile.
    while ( high - low > 1)
    {
        c_low <- cdf(low)
        c_mid <- cdf(low+floor((high-low)/2))
        c_high <- cdf(high)

        c_min <- min(min(abs(0.95-c_low), abs(0.95-c_mid)), abs(0.95-c_high))

        if ( c_mid > 0.95 ) {
            high <- high - floor((high-low)/2)
            print (sprintf("adjust high: %s\n", high));
        } else if ( c_mid <= 0.95 ) {
            low <- low + floor((high-low)/2)
            print (sprintf("adjust low: %s\n", low));
        }

        #swap<-0
        #if ( c_min == abs(0.95-c_mid) ) {
        #    # is it in top half or bottom half?
        #    print (sprintf("middle\n"));
        #    if ( abs(0.95-c_low) < abs(0.95-c_high) ) {
        #        low <- low + floor((high-low)/2)
        #        print (sprintf("adjust low: %s\n", low));
        #    } else { #if ( c_min == abs(0.95-c_high) ) {
        #        high <- high - floor((high-low)/2)
        #        print (sprintf("adjust high: %s\n", high));
        #    }
        #} else {
        #    if ( c_min == abs(0.95-c_low) ) {
        #        high <- high - floor((high-low)/2)
        #        print (sprintf("adjust high: %s\n", high));
        #    } else { #if ( c_min == abs(0.95-c_high) ) {
        #        low <- low + floor((high-low)/2)
        #        print (sprintf("adjust low: %s\n", low));
        #    }
        #}
    }
    return (low)
}

#0,193-402,length(r)
ttr1 <- time_to_reboot(image,9,122)
ttr2 <- time_to_reboot(image,131,223)

ttr8 <- time_to_reboot(image2,0,193)
ttr9 <- time_to_reboot(image2,402)

x1 <- ecdf(c(ttr1, ttr2))
x2 <- ecdf(c(ttr8,ttr9))
start_image("reboot_ttr_cdf.png")
plot(x1, col.vert='red', col.hor="red", col.points="red", pch='*', xlab="Days to Reboot", ylab="Percentile", verticals=TRUE, xlim=c(0,170), main="CDF of Days to Reboot for BM & API Events")
plot(x2, col.vert='blue', col.hor="blue", col.points="blue", pch=20, verticals=TRUE, add=TRUE)
legend(130, 0.15, legend=c("BM Uploads", "API Events"), col=c('red', 'blue'), pch=c(42, 20))
abline(0.95,0)
v1<-find_95(x1)
v2<-find_95(x2)
abline(v=v1, col="pink")
abline(v=v2, col="light blue")
axis(1, labels=c(v1,v2), at=c(v1,v2))

abline(v=7, col="grey")
abline(v=14, col="grey")
abline(v=21, col="grey")
abline(v=28, col="grey")
abline(v=42, col="grey")
abline(v=56, col="grey")
end_image()

e <- reboot_events(image)
e2 <- reboot_events(image2)
x1 <- ecdf(e)
x2 <- ecdf(e2)

start_image("reboot_days_cdf.png")
plot(x1, col.vert='red', col.hor="red", col.points="red", pch='*', xlab="Reboots in a Single Day", ylab="Percentile", verticals=TRUE, xlim=c(0,100), main="CDF of Reboots per Day for BM & API Events")
plot(x2, col.vert='blue', col.hor="blue", col.points="blue", pch=20, verticals=TRUE, add=TRUE)
legend(75, 0.15, legend=c("BM Uploads", "API Events"), col=c('red', 'blue'), pch=c(42, 20))
abline(0.95,0)
v1<-find_95(x1)
v2<-find_95(x2)
abline(v=v1, col="pink")
abline(v=v2, col="light blue")
axis(1, labels=c(v1,v2), at=c(v1,v2))
end_image()



f <- reboot_frequency(image)
f2 <- reboot_frequency(image2)
x1 <- ecdf(f)
x2 <- ecdf(f2)

start_image("reboot_node_cdf.png")
par(mfrow=c(1,1))
par(mai=c(.9,.8,.5,.4))
plot(x1, col.vert='red', col.hor="red", col.points="red", pch='*', xlab="Reboots per Node", ylab="Percentile", verticals=TRUE, xlim=c(0,100), main="CDF of Reboot per Node for BM & API Events")
plot(x2, col.vert='blue', col.hor="blue", col.points="blue", pch=20, verticals=TRUE, add=TRUE)
legend(75, 0.15, legend=c("BM Uploads", "API Events"), col=c('red', 'blue'), pch=c(42, 20))
abline(0.95,0)
v1<-find_95(x1)
v2<-find_95(x2)
abline(v=v1, col="pink")
abline(v=v2, col="light blue")
axis(1, labels=c(v1,v2), at=c(v1,v2))
end_image()



par(mfrow=c(1,1))
par(mai=c(.7,.7,.7,.7))
