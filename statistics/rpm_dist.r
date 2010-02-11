#####

#system("URL='https://monitor.planet-lab.org:443/monitor/query?object=nodes&nodehistory_hostname=&hostname=on&observed_status=on&rpms=on&rpmvalue=planetlab&tg_format=plain'; curl -s --insecure $URL | grep -v DOWN | grep -v DEBUG | /usr/share/monitor/statistics/hn2rpms.py > out_rpm.csv");
#system("grep MD5SUMS /usr/share/monitor/monitor.log | grep -v measurement-lab | awk 'BEGIN { printf \"hostname,yumsum\\n\" } {if ( $3 != \"\") { printf \"%s,%s\\n\", $2,$3 } }' > yumsum.csv")

r <- read.csv("out_rpm.csv")
ys<- read.csv('yumsum.csv')
m<-merge(r,ys, by="hostname")

s<-table(factor(r$NodeManager), factor(r$kernel), factor(r$iptables));
plot(s);

ideal<-c(NodeManager='NodeManager-1.8-12.planetlab.1',
      	 NodeUpdate='NodeUpdate-0.5-4.planetlab', 
		 codemux='codemux-0.1-13.planetlab',
      	 fprobe.ulog='fprobe-ulog-1.1.3-0.planetlab', 
		 ipod='ipod-2.2-1.planetlab',
      	 iproute='iproute-2.6.16-2.planetlab', 
		 iptables='iptables-1.3.8-9.planetlab',
         kernel='kernel-2.6.22.19-vs2.3.0.34.39.planetlab',
      	 madwifi='madwifi-0.9.4-2.6.22.19.3.planetlab', 
		 monitor.client='monitor-client-3.0-17.planetlab',
      	 monitor.runlevelagent='monitor-runlevelagent-3.0-17.planetlab', 
		 pl_mom='pl_mom-2.3-1.planetlab',
      	 pl_sshd='pl_sshd-1.0-11.planetlab', 
		 pyplnet='pyplnet-4.3-3.planetlab',
      	 util.vserver.pl='util-vserver-pl-0.3-17.planetlab',
      	 vserver.planetlab.f8.i386='vserver-planetlab-f8-i386-4.2-12.2009.06.23',
      	 vserver.systemslices.planetlab.f8.i386='vserver-systemslices-planetlab-f8-i386-4.2-12.2009.06.23',
      	 vsys='vsys-0.9-3.planetlab', 
		 vsys.scripts='vsys-scripts-0.95-11.planetlab');

r_summary <- lapply(r[,4:23], summary)
for (i in 1:length(r_summary))
{
    n<-sort(unlist(r_summary[i]), decreasing=TRUE)
	names(n[1])
}

as.numeric(factor(ideal[1], levels(r$NodeManager)))

cv <- function ( row , rows=566, start_col=4, end_col=23, ref=NULL)
{
	ret<-NULL;
    for ( i in 1:rows )
	{
		r_l <-NULL
	    for ( name in names(row) ) 
		{
			# NOTE: this doesn't work unless the levels in row are a subset of ref's levels.
 			x<-as.numeric(factor(row[i,name], levels(factor(unlist(row[name])))));
			r_l <- c(r_l, x);
		}
		#r<-as.numeric(row[i,start_col:end_col]);
		str<- paste(as.character(r_l), collapse="-", sep="-");
		ret<- rbind(ret, str);
	}
	return (ret);
}

grow <- function (d, column, val)
{
    r <- which(d[column] == val);
	return (d[r,]);
}

cv(m, length(m$hostname));
i<-data.frame(t(ideal));
cv(i, 1, 1, length(ideal));

	# ---

x<-cv(r, length(r$hostname))
x2<-factor(x)
# plot the frequency of each RPM package combination
barplot(sort(table(x2), decreasing=TRUE), 
		ylim=c(0, max(table(x2))),
		xlab="Unique Package Combinations",
		ylab="Frequency",
		axisnames=FALSE,
		main=paste("Distribution of Packages for", length(r$hostname),"nodes"));

png("/Users/soltesz/Downloads/rpm_plpackages_distribution_1.png",
	width=640,
	height=300,
	unit="px")
# 1x1 grid, with 1" margins on the bottom/left, 0.5" on the top/right
par(mfrow=c(1,1));
par(mai=c(1,1,0.5,0.5));
barplot(sort(table(x2), decreasing=TRUE), 
		ylim=c(0, max(table(x2))),
		xlab="Unique Package Combinations",
		ylab="Frequency",
		axisnames=FALSE,
		main=paste("Distribution of Packages for", length(r$hostname),"nodes"));
dev.off()



#convert_rpm <- function ( row )
#{
#	c <- as.character(row$rpms)
#	rpm_list <- unlist(strsplit(c, " "))
#	rpm_sort <- paste(sort(rpm_list), collapse="::");
#	return (rpm_sort);
#}

#s<-convert_rpm(r)

#for ( row in r[,] )
#{
#	c <- as.character(row$rpms)
#	rpm_list <- unlist(strsplit(c, " "))
#	row$rpm_sort <- paste(sort(rpm_list), collapse="::");
#
#	#for ( rpm in rpm_list ) 
#	#{
#	#	fields <- unlist(strsplit(rpm, "-"));
#	#	s <- sort(fields);
#	#}
#}
#
#s<-sort(rpm_list);


