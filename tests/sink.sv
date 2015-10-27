module sink(
               input  logic [63:0] din,
               output logic [63:0] dout
               );

  always_comb begin
     dout <= ~din;
  end
endmodule
