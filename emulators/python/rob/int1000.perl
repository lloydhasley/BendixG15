#!/usr/bin/perl

my %mem;	# the memory
my %memtype;	# 'd' or 'i' for data or instruction
my %indexreg;	# $indexreg{ ir#, [cw]{base,diff,lim} }
my $pc;		# current instruction loc
my $nextpc;	# next instruction loc
my $ar;		# value of accumulator
my $addr;	# address stored in current instruction
my $effaddr;	# address after IR added
my $ir;		# index_register number stored in current instruction
my $trace = 0;
my $ninstr = 0;
my $op;

# instruction: mem{addr} is a hash with keys 'ind','op','addr'
# ... of lengths 1, 2, and 4

# data: mem{addr} has a floating point number


    # &c(addr) returns data from addr
sub c {
    my $address = shift;
    if (!defined ($memtype{$address}) ) {
	die "addr $address has undefined data value, pc=$pc op=$op inst=$ir.$op.$addr";
    }
    if ($memtype{$address} ne 'd') {
	die "addr $address has type '$memtype{$address}'; want data; pc=$pc op=$op inst=$ir.$op.$addr";
    }
    return $mem{$address};
}

    # puts data into memory; marks as 'data'
sub store {
    my ($addr, $val) = @_;
    if ($memtype{$addr} eq 'i') {
	die "storing data over instruction at addr $addr";
    }
    $mem{$addr} = $val;
    $memtype{$addr} = 'd';
}

sub op20 { $nextpc = $effaddr if $ar >= 0; }
sub op22 { $nextpc = $effaddr if $ar < 0 ; }
sub op23 { $nextpc = $effaddr if $ar == 0; }
sub op29 { $nextpc = $effaddr            ; }

sub op31 { print $effaddr, "	"; }

sub op40 { $ar  = -&c($effaddr); }
sub op41 { $ar -= &c($effaddr); }
sub op42 {
$ar  = &c($effaddr);
# if ($ir) {print "\n$pc: 42.$addr \@$effaddr -> $ar  [1502:", &c("1502"), "]\n";}
}
sub op43 {
    if (c($effaddr) > 1099511627776) {
	$ar = int($ar);
    }
    $ar += &c($effaddr);
}
sub op44 { $ar *= &c($effaddr); }
sub op45 { $ar  = abs(&c($effaddr)); }
# sub op46 { }
sub op47 { $ar  = &c($effaddr) / $ar; }
sub op48 { $ar /= &c($effaddr); }
sub op49 { &store ($effaddr, $ar); }

sub op30 {
    my $t = sprintf("%04d", $effaddr);
    my $ntb = substr($t, 0, 2) + 0;
    my $ncr = substr($t, 2, 2) + 0;
    print "\n" x $ncr if $ncr > 0;
    print "	" x $ntb if $ntb > 0;
}
sub op33 { printf ("%5g\t", &c($effaddr)); }
sub op38 { printf ("%5g\n", &c($effaddr)); }

sub op63 { $| = 1; print ""; $| = 0;}
sub op67 {
    print "Total $ninstr instructions executed.\n";
    exit (0);
}

sub op70 { $indreg{$ir,'wbase'} = $addr; }
sub op71 { $indreg{$ir,'wdiff'} = $addr % 100; }
sub op72 { $indreg{$ir,'wlim'}  = $addr % 100; }
sub op73 { $indreg{$ir,'cbase'} = int ($addr/100) * 100; }
sub op74 { $indreg{$ir,'cdiff'} = int ($addr/100) * 100; }
sub op75 { $indreg{$ir,'clim'}  = int ($addr/100) * 100; }
sub op76 {
    $indreg{$ir,'wbase'} += $indreg{$ir,'wdiff'};
    $nextpc = $addr if $indreg{$ir,'wbase'} <= $indreg{$ir,'wlim'};
}
sub op77 {
    $indreg{$ir,'cbase'} += $indreg{$ir,'cdiff'};
    $nextpc = $addr if $indreg{$ir,'cbase'} <= $indreg{$ir,'clim'};
}
sub op98 { $trace = $effaddr; }
sub op99 {
    $| = 1; print "[$addr]"; $| = 0;
}

sub listinst {
    my $addr = shift;
    my $irx = $mem{$addr}->{'ir'} || " ";
    my $opx = $mem{$addr}->{'op'};
    my $adx = $mem{$addr}->{'addr'};
    printf ("%4d: %s.%s.%s\n", $addr, $irx, $opx, $adx);
}

sub compile {
    while (<>) {
	chomp;
	if (/SET/) {
	    my ($x, $addr, $x, $val) = split;
	    $addr = sprintf("%04d", $addr);
	    $val =~ s,/,.,;
	    &store ($addr, eval($val));
	} else {
	    my ($addr, $instr) = split (/\s+/);
	    $addr =~ s/://;
	    $addr = sprintf("%04d", $addr);
	    my ($ir,$op,$inaddr) = split (/\./, $instr);
	    $inaddr = sprintf ("%04d", $inaddr);
	    if (!defined (&{'op'.$op})) {
		die "$addr: opcode '$op' not implemented";
	    }
	    $memtype{$addr} = 'i';
	    $mem{$addr} = {'ir'=>$ir, 'op'=>$op, 'addr'=>$inaddr};
	}
    }
}

&compile;


my @opnoodds = (40, 41, 42, 43, 44, 45, 47, 48, 40, 50, 51, 52, 33,
		38, 32, 34, 55, 39);
my %opnoodds;
foreach (@opnoodds) { $opnoodds[$_] = 1; }

# execution loop:
$pc = "0900";
$ar = rand(1000000);
while (1) {
    $nextpc = sprintf("%04d", $pc + 1);
    if ($memtype{$pc} ne 'i') {
	die "pc=$pc; memtype must be 'i'; got '$memtype{$pc}'";
    }
    my $t = $mem{$pc};
    $op = $t->{'op'};
    $addr = $t->{'addr'};
    $ir = $t->{'ir'};
    $effaddr = $addr;
    $effaddr += $indreg{$ir,'cbase'} + $indreg{$ir,'wbase'} if $ir;
    $effaddr = sprintf("%04d", $effaddr);
    if ( ($effaddr & 1) && $opnoodds[$op]) {
	die "effective address is odd!  \@$pc";
    }
    &store ($addr, $ar) if $effaddr eq '2100';
    if ($trace) {
	print "$pc: ", ($ir||" "), ".$op.$addr";
	if ($addr ne $effaddr && ($op < 70 || $op > 79) ) {
	    print "  [\@$effaddr]";
	}
    }
    &{'op'.$op};
    if ($ir) {
	if ($indreg{$ir,'wbase'} > 100) {
	    die "index register $ir > 100   $addr: $ir.$op.$addr";
	}
    }
    $ninstr++;
    if ($trace) {
#	my $packed = pack('d', $ar);        # pack as double (float)
#	my $hex = unpack('H*', $packed);    # packed binary to hex string
#	my @bytes = ($hex =~ /../g);
#	@bytes = reverse @bytes;
#	my $reversed = join('', @bytes);
#	print "  AR: $ar [$reversed]\n";
	printf "  AR: $ar [0x%x]", $ar;
	if ($ir) {
	    print "  IR${ir}: ", $indreg{$ir,'cbase'}/100, ".$indreg{$ir,'wbase'}";
	}
	print "\n";
    }
    $pc = $nextpc;
}
