// Just a, b, c
// line above is expected output

// normal completion on component

model m
	model A

		model shoul_not_be_in_completion
			
		end shoul_not_be_in_completion;
		
		Real a;
		Real b;
		Real c;
	end A;

	A aa;
	
equation

	aa^ = 10;
		
end m;