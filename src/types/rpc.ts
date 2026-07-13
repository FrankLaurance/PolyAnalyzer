export type AnalyzerName = "gpc" | "mw" | "dsc" | "ir" | "other" | "system";

interface FileListParams {
  datadir: string;
}

interface FileListResult {
  files: string[];
}

interface PlotStyleParams {
  line_width?: number;
  axis_width?: number;
  title_font_size?: number;
  axis_font_size?: number;
  transparent_back?: boolean;
}

interface AnalyzeResult {
  success: boolean;
}

export interface RpcContract {
  "system.get_default_datapath": {
    params: Record<string, never>;
    result: { datapath: string };
  };
  "system.get_default_ir_datapath": {
    params: Record<string, never>;
    result: { datapath: string };
  };
  "system.clean_output": {
    params: { datadir: string; confirm: true };
    result: { success: boolean; cleaned: string[] };
  };
  "settings.list": {
    params: { type: "mw" | "dsc" | "ir" };
    result: { settings: string[] };
  };
  "settings.load": {
    params: { type: "mw" | "dsc" | "ir"; name: string };
    result: { setting: Record<string, unknown> };
  };
  "settings.save": {
    params: {
      type: "mw" | "dsc" | "ir";
      name: string;
      setting: Record<string, unknown>;
    };
    result: { success: boolean };
  };
  "settings.delete": {
    params: { type: "mw" | "dsc" | "ir"; name: string };
    result: { success: boolean };
  };
  "gpc.list_files": { params: FileListParams; result: FileListResult };
  "mw.list_files": { params: FileListParams; result: FileListResult };
  "dsc.list_files": { params: FileListParams; result: FileListResult };
  "ir.list_files": { params: FileListParams; result: FileListResult };
  "gpc.analyze": {
    params: {
      datadir: string;
      output_filename: string;
      selected_files?: string[];
      save_file: boolean;
      save_picture: boolean;
      display_mode: boolean;
      save_figure_file_gpc: boolean;
      confirm_overwrite: boolean;
    };
    result: AnalyzeResult & { output_dir: string };
  };
  "mw.analyze": {
    params: PlotStyleParams & {
      datadir: string;
      selected_files: string[];
      save_picture: boolean;
      display_picture: boolean;
      segmentpos: number[];
      bar_color: string;
      mw_color: string;
      bar_width: number;
      draw_bar: boolean;
      draw_mw: boolean;
      draw_table: boolean;
    };
    result: AnalyzeResult & { output_dir: string };
  };
  "dsc.analyze": {
    params: PlotStyleParams & {
      datadir: string;
      selected_files: string[];
      save_seg_mode: boolean;
      draw_seg_mode: boolean;
      draw_cycle: boolean;
      display_pic: boolean;
      save_cycle_pic: boolean;
      peaks_upward: boolean;
      center_peak: boolean;
      left_length: number;
      right_length: number;
      curve_color: string;
    };
    result: AnalyzeResult & { cycle_dir: string; pic_dir: string };
  };
  "ir.analyze": {
    params: PlotStyleParams & {
      datadir: string;
      selected_files: string[];
      curve_color: string;
      draw_overlay: boolean;
      normalize_overlay: boolean;
      normalization_peak: number;
    };
    result: AnalyzeResult & {
      output_dir: string;
      generated_files: string[];
      processed_count: number;
    };
  };
}

export type RpcMethod = keyof RpcContract;
export type RpcParams<M extends RpcMethod> = RpcContract[M]["params"];
export type RpcResult<M extends RpcMethod> = RpcContract[M]["result"];
export type FileListMethod = Extract<RpcMethod, `${string}.list_files`>;

export type SendRpcRequest = <M extends RpcMethod>(
  method: M,
  params: RpcParams<M>,
) => Promise<RpcResult<M>>;
