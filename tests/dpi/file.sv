module m();
   import "DPI-C" pure function void xsimintf_init ();
   import "DPI-C" pure function void xsimintf_export (input string s);
   import "DPI-C" pure function string xsimintf_import ();
   import "DPI-C" pure function int xsimintf_wait ();

   logic clk = 0;
   logic data = 0;
   //logic i, j;
   logic [31:0] data_bus = 32'hfafafafa;
   integer      delay = 20;

   initial
     begin
        xsimintf_init();
    end

   always begin
      automatic string       strexp = "INIT";

      delay = xsimintf_wait();
      #delay;
      $display("Finished waiting: %d", delay);
      strexp = xsimintf_import();
      $display("IMPORTED: %s", strexp);
      $sscanf(strexp, "%d", clk);
   end

   always_comb begin
      automatic string       strexp = "INIT";

      $sformat(strexp, "Data: %h, Data_bus: %h",data, data_bus);
      xsimintf_export(strexp);
      $display("EXPORTED: %s", strexp);
      strexp = xsimintf_import();
      $display("IMPORTED: %s", strexp);
      $sscanf(strexp, "%d", clk);
   end

   always @ (posedge clk) begin
      data <= !data;
      $display(data);

   end
endmodule
