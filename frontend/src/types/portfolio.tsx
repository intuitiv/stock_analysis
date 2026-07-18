import React from 'react';

export interface Position {
  id: number;
  stock_id: number;
  symbol: string;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
  current_price?: number;
  value?: number;
  gain_loss?: number;
  gain_loss_percent?: number;
}

export interface Portfolio {
  id: string;
  name: string;
  user_id: number; // Or string
  created_at: string;
  updated_at: string;
  positions: Position[];
  total_value?: number;
  day_change_value?: number;
  day_change_percent?: number;
  total_gain_loss_value?: number;
  total_gain_loss_percent?: number;
}

export interface PortfolioListData {
  id: string;
  name: string;
  // Add other summary fields if your /portfolios endpoint returns them
}