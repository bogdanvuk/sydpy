module sink(
               input  logic [7:0] din,
               output logic [7:0] dout
               );

  always_comb begin
     dout <= ~din;
  end
endmodule
